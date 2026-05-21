# backend/monitoring/risk_engine.py
"""
Risk Engine — Intelligent Transaction Risk Classification
=========================================================
Severity tiers:
  SAFE    (score 0.0–0.40) → log only, no alerts sent
  WARNING (score 0.40–0.70) → logged in UI feed, no external alerts
  HIGH    (score 0.70+)    → full alert: Supabase, WebSocket, Telegram, Email

Dual-model approach:
  Model 1: Rule-based heuristics (explicit suspicious field detection)
  Model 2: Isolation Forest (statistical anomaly, only after 10+ tx baseline)
  Model 3: Random Forest ML classifier (AI classification)

A transaction must score HIGH to trigger external notifications.
"""
import logging
from typing import Dict, Any, List, Optional

from ml_models.anomaly import get_monitor
from utils.ai_analyzer import analyze_transaction

logger = logging.getLogger(__name__)

# ── Thresholds ──────────────────────────────────────────────────────────────
SAFE_THRESHOLD    = 0.35   # Below this -> SAFE, no alert
WARNING_THRESHOLD = 0.60   # 0.35-0.60  -> WARNING (logged in feed, no external alert)
# Above 0.60 -> HIGH, triggers Telegram/Email

# ── Rule-based suspicious indicators ────────────────────────────────────────
LARGE_PAYMENT_MICROALGOS = 10_000_000_000   # 10,000 ALGO
HIGH_FEE_MICROALGOS      = 10_000           # 10× min fee
MAX_INNER_TXNS           = 10


def _rule_based_score(txn: Dict[str, Any]) -> tuple[float, List[str]]:
    """
    Calculate a heuristic risk score from known suspicious Algorand patterns.
    Returns (score: float 0-1, flags: list[str])
    """
    score = 0.0
    flags: List[str] = []
    pay = txn.get("payment-transaction", {}) or {}

    # Hard flags (very suspicious - each alone crosses HIGH threshold)
    if txn.get("rekey-to"):
        score += 0.70   # REKEY alone -> HIGH (0.70 * 0.60 = 0.42, WARNING; but pairs push to HIGH)
        flags.append("[CRITICAL] REKEY operation detected - account control transfer")

    if pay.get("close-remainder-to"):
        score += 0.65   # Drain pattern
        flags.append("[CRITICAL] CLOSE_REMAINDER_TO detected - account draining pattern")

    # Soft flags (suspicious but not decisive alone)
    amount = pay.get("amount", 0) or 0
    if amount > LARGE_PAYMENT_MICROALGOS:
        score += 0.35
        flags.append(f"Large transfer: {amount / 1_000_000:.1f} ALGO")

    fee = txn.get("fee", 1000) or 1000
    if fee > HIGH_FEE_MICROALGOS:
        score += 0.20
        flags.append(f"Unusually high fee: {fee} microAlgos")

    inner_count = len(txn.get("inner-txns", []) or [])
    if inner_count > MAX_INNER_TXNS:
        score += 0.25
        flags.append(f"High inner-txn count: {inner_count}")

    # Failed transactions (application calls that fail suggest probing)
    if txn.get("application-transaction") and txn.get("global-state-delta") is None:
        score += 0.15
        flags.append("Failed application call — possible probe/exploit attempt")

    return min(score, 1.0), flags


def _isolation_score(anomaly_result: Dict[str, Any]) -> float:
    """Map Isolation Forest result to a 0-1 score contribution."""
    if not anomaly_result.get("is_anomaly"):
        return 0.0
    raw_score = anomaly_result.get("anomaly_score", 0.0)
    # Scale to 0.30–0.70 range so IF alone can only produce WARNING
    return 0.30 + (raw_score * 0.40)


def _ml_score(ai_result: Dict[str, Any]) -> float:
    """Map Random Forest AI classification to a 0-1 score contribution."""
    label = ai_result.get("label", "SAFE")
    if label == "RISKY":
        return 0.65
    if label == "SUSPICIOUS":
        return 0.40
    return 0.0


def _severity_from_score(score: float) -> str:
    if score >= WARNING_THRESHOLD:
        return "HIGH"
    if score >= SAFE_THRESHOLD:
        return "WARNING"
    return "SAFE"


def evaluate_transaction_risk(
    job_id: str,
    txns: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Evaluate a list of transactions and return a result record for EVERY
    transaction (not just flagged ones), so the frontend feed always updates.

    Each record has:
      txn_id, severity, score, description, should_alert, ai_label
    """
    if not txns:
        return []

    monitor = get_monitor(str(job_id))
    # Feed new txns to Isolation Forest history (trains after 10 samples)
    monitor.add_transactions(txns)

    results = []

    for txn in txns:
        txn_id = txn.get("id", "UNKNOWN")
        try:
            # ── Model 1: Rule-based heuristics ──────────────────────────
            rule_score, rule_flags = _rule_based_score(txn)

            # ── Model 2: Isolation Forest ────────────────────────────────
            anomaly_result = monitor.check_transaction(txn)
            if_score = _isolation_score(anomaly_result)

            # ── Model 3: AI Random Forest ────────────────────────────────
            ai_result = analyze_transaction(txn)
            ml_score = _ml_score(ai_result)

            # ── Combine scores (weighted: rules dominate, IF supplements) ─
            # Rule heuristics = 60%, IF = 25%, ML = 15%
            combined_score = round(
                (rule_score * 0.60) + (if_score * 0.25) + (ml_score * 0.15),
                3
            )

            severity = _severity_from_score(combined_score)

            # Build description from most informative source
            if rule_flags:
                description = " | ".join(rule_flags)
            elif combined_score >= SAFE_THRESHOLD:
                description = anomaly_result.get("description") or ai_result.get("error") or "Statistical anomaly"
            else:
                tx_type = txn.get("tx-type", "pay")
                description = f"Normal {tx_type} transaction — no suspicious indicators"

            # Only alert externally for HIGH severity
            should_alert = severity == "HIGH"

            result = {
                "txn_id":       txn_id,
                "severity":     severity,
                "score":        combined_score,
                "description":  description,
                "should_alert": should_alert,
                "ai_label":     ai_result.get("label", "SAFE"),
                "ai_risk_level":ai_result.get("risk_level", "SAFE"),
                "anomaly_score":anomaly_result.get("anomaly_score", 0.0),
            }
            results.append(result)

            logger.debug(
                f"[RiskEngine] txn={txn_id} score={combined_score:.3f} "
                f"severity={severity} flags={rule_flags}"
            )

        except Exception as e:
            logger.error(f"[RiskEngine] Error evaluating txn {txn_id}: {e}")
            # Still emit a SAFE result so the feed updates
            results.append({
                "txn_id":       txn_id,
                "severity":     "SAFE",
                "score":        0.0,
                "description":  f"Evaluation error: {e}",
                "should_alert": False,
                "ai_label":     "UNKNOWN",
                "ai_risk_level":"UNKNOWN",
                "anomaly_score":0.0,
            })

    return results


def evaluate_contract_baseline(contract_address: str, txns: List[Dict[str, Any]]) -> tuple[str, str, float]:
    """
    Examines a list of recent transactions (up to 50) and determines
    overall contract status: SAFE, LOW RISK, WARNING, HIGH RISK, VULNERABLE, SUSPICIOUS, INACTIVE.
    """
    if not txns:
        return "INACTIVE", "No recent activity detected on the blockchain for this address.", 0.0

    total_count = len(txns)
    failed_count = 0
    rekey_count = 0
    drain_count = 0
    large_transfer_count = 0
    high_fee_count = 0
    inner_txn_count = 0
    
    for txn in txns:
        pay = txn.get("payment-transaction", {}) or {}
        
        # Check failed calls
        if txn.get("application-transaction") and txn.get("global-state-delta") is None:
            failed_count += 1
            
        # Check rekeys
        if txn.get("rekey-to"):
            rekey_count += 1
            
        # Check draining
        if pay.get("close-remainder-to"):
            drain_count += 1
            
        # Check large amount
        amount = pay.get("amount", 0) or 0
        if amount > LARGE_PAYMENT_MICROALGOS:
            large_transfer_count += 1
            
        # Check high fees
        fee = txn.get("fee", 1000) or 1000
        if fee > HIGH_FEE_MICROALGOS:
            high_fee_count += 1
            
        # Check inner transactions
        inner_count = len(txn.get("inner-txns", []) or [])
        if inner_count > MAX_INNER_TXNS:
            inner_txn_count += 1

    # Classify based on severity of findings
    if rekey_count > 0:
        return "HIGH RISK", "Vulnerable control transfer. Rekey operation detected on this contract address.", 0.95
    if drain_count > 0:
        return "VULNERABLE", "Account draining pattern. CLOSE_REMAINDER_TO detected in recent payments.", 0.90
    if failed_count > 3:
        return "WARNING", f"Suspicious activity. Found {failed_count} repeated failed application calls recently.", 0.65
    if large_transfer_count > 0 and high_fee_count > 0:
        return "SUSPICIOUS", "Atypical activity. Detected large transfers with unusually high transaction fees.", 0.55
    if failed_count > 0:
        return "LOW RISK", f"Minor issues. Detected {failed_count} failed transaction call(s) recently.", 0.38
    if large_transfer_count > 0:
        return "LOW RISK", f"Minor warning. Large transfer of {large_transfer_count} transactions detected.", 0.35
    
    return "SAFE", f"No suspicious activity detected in the last {total_count} transactions.", 0.05


