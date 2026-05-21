# backend/monitoring/monitor_service.py
"""
Monitor Service — Core async monitoring loop
=============================================
Handles:
  - Address validation before hitting the Algorand indexer
  - Per-job transaction deduplication (never re-process same txn)
  - Per-contract alert cooldown (prevents SMTP/Telegram spam)
  - Severity-gated external alerts:
      SAFE    -> WebSocket feed only (green, no DB write)
      WARNING -> WebSocket + Supabase (yellow, no Telegram/Email)
      HIGH    -> WebSocket + Supabase + Telegram + Email (with cooldown)
"""
import re
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set

from utils.supabase_client import get_supabase_client
from monitoring.transaction_fetcher import fetch_new_transactions, get_highest_round
from monitoring.risk_engine import evaluate_transaction_risk
from monitoring.alert_manager import dispatch_alerts

logger = logging.getLogger(__name__)

# ── Address validation ──────────────────────────────────────────────────────
# Algorand account addresses: 58-char base32 (uppercase + 2-7)
# Application IDs: numeric strings (we monitor by app_id as string)
_ALGO_ADDR_RE = re.compile(r'^[A-Z2-7]{58}$')
_NUMERIC_RE = re.compile(r'^\d+$')

def _is_valid_address(addr: str) -> bool:
    """Return True only for real Algorand addresses or numeric app IDs."""
    if not addr:
        return False
    return bool(_ALGO_ADDR_RE.match(addr)) or bool(_NUMERIC_RE.match(addr))


# ── In-memory deduplication state ──────────────────────────────────────────
# Maps job_id -> set of already-processed txn IDs
_seen_txn_ids: Dict[str, Set[str]] = {}

# Maps contract_address -> datetime of last HIGH alert sent
_last_high_alert: Dict[str, datetime] = {}

# Minimum time between HIGH alerts per contract
ALERT_COOLDOWN_MINUTES = 5


def _is_seen(job_id: str, txn_id: str) -> bool:
    return txn_id in _seen_txn_ids.get(job_id, set())


def _mark_seen(job_id: str, txn_id: str):
    if job_id not in _seen_txn_ids:
        _seen_txn_ids[job_id] = set()
    _seen_txn_ids[job_id].add(txn_id)


def _is_on_cooldown(contract_address: str) -> bool:
    last = _last_high_alert.get(contract_address)
    if last is None:
        return False
    return datetime.utcnow() - last < timedelta(minutes=ALERT_COOLDOWN_MINUTES)


def _set_cooldown(contract_address: str):
    _last_high_alert[contract_address] = datetime.utcnow()


async def _broadcast(payload: dict, app_id: int = 0):
    """Push event to all connected WebSockets."""
    try:
        from monitoring.monitoring_manager import manager
        await manager.broadcast_alert(app_id, payload)
    except Exception as e:
        logger.warning(f"[Monitor] WebSocket broadcast failed: {e}")


async def process_monitoring_job(job: dict):
    """
    Process a single monitoring job iteration asynchronously.
    Schema: contract_address, status, last_txn, email
    """
    job_id = job["id"]
    contract_address = job["contract_address"]
    last_txn = job.get("last_txn", 0) or 0
    
    # Parse delimited email, telegram chat id, and app_id from email column
    email_val = job.get("email", "") or ""
    alert_email = ""
    telegram_chat_id = None
    app_id = 0
    if "##" in email_val:
        parts = email_val.split("##")
        alert_email = parts[0]
        if len(parts) > 1 and parts[1]:
            telegram_chat_id = parts[1]
        if len(parts) > 2 and parts[2]:
            try:
                app_id = int(parts[2])
            except ValueError:
                app_id = 0
    else:
        alert_email = email_val

    # ── Validate address BEFORE hitting Algorand indexer ─────────────────────
    # Invalid addresses (test data, placeholder text) cause 400 errors from
    # the indexer. Auto-deactivate to keep the loop clean and logs quiet.
    if not _is_valid_address(contract_address):
        logger.warning(
            f"[Monitor] Auto-deactivating invalid address '{contract_address}' "
            f"(job={job_id[:8]}...) — must be 58-char Algorand addr or numeric ID"
        )
        try:
            supabase = get_supabase_client()
            await asyncio.to_thread(
                lambda: supabase.table("monitored_contracts")
                .update({"status": "inactive"})
                .eq("id", job_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"[Monitor] Failed to deactivate invalid job {job_id}: {e}")
        return

    try:
        # 1. Fetch new transactions
        new_txns = await fetch_new_transactions(contract_address, last_txn)
        if not new_txns:
            return

        # 2. Deduplicate — skip already-processed txns
        fresh_txns = []
        for txn in new_txns:
            tid = txn.get("id", "")
            if tid and _is_seen(job_id, tid):
                logger.debug(f"[Monitor] Skipping duplicate txn: {tid}")
                continue
            fresh_txns.append(txn)
            if tid:
                _mark_seen(job_id, tid)

        if not fresh_txns:
            logger.debug(
                f"[Monitor] All {len(new_txns)} txns already processed for {contract_address}"
            )
            # Still update the round pointer so we don't re-fetch old blocks
            highest_round = get_highest_round(new_txns, last_txn)
            if highest_round > last_txn:
                supabase = get_supabase_client()
                await asyncio.to_thread(
                    lambda: supabase.table("monitored_contracts").update(
                        {"last_txn": highest_round + 1}
                    ).eq("id", job_id).execute()
                )
            return

        logger.info(f"[Monitor] Processing {len(fresh_txns)} fresh txns for {contract_address}")

        # 3. Evaluate risk on fresh transactions only
        results = await asyncio.to_thread(evaluate_transaction_risk, job_id, fresh_txns)

        # 4. Handle each result by severity
        supabase = get_supabase_client()
        high_alert_count = 0

        for result, txn in zip(results, fresh_txns):
            severity = result["severity"]
            description = result["description"]
            score = result["score"]
            txn_id = result["txn_id"]

            # Build WebSocket payload for live feed (ALL severities go through)
            ws_payload = {
                "txn_id":      txn_id,
                "severity":    severity,
                "score":       score,
                "description": description,
                "timestamp":   datetime.utcnow().isoformat(),
                "contract":    contract_address,
            }
            await _broadcast(ws_payload, app_id)

            if severity == "SAFE":
                logger.info(f"[Monitor] OK txn={txn_id[:12]}... | {description[:70]}")
                continue  # No DB insert, no external alert

            if severity == "WARNING":
                logger.info(f"[Monitor] WARNING txn={txn_id[:12]}... score={score:.3f}")
                alert_row = {
                    "contract_address": contract_address,
                    "message":          description,
                    "risk_level":       "WARNING",
                    "timestamp":        datetime.utcnow().isoformat(),
                }
                await asyncio.to_thread(
                    lambda r=alert_row: supabase.table("alerts").insert(r).execute()
                )
                continue  # No Telegram/Email for WARNING

            # HIGH: full pipeline
            if severity == "HIGH":
                logger.warning(
                    f"[Monitor] HIGH RISK txn={txn_id[:12]}... "
                    f"score={score:.3f} | {description[:80]}"
                )
                alert_row = {
                    "contract_address": contract_address,
                    "message":          description,
                    "risk_level":       "HIGH",
                    "timestamp":        datetime.utcnow().isoformat(),
                }
                await asyncio.to_thread(
                    lambda r=alert_row: supabase.table("alerts").insert(r).execute()
                )

                # Cooldown check: prevent Telegram/Email spam
                if _is_on_cooldown(contract_address):
                    logger.info(
                        f"[Monitor] HIGH alert suppressed (cooldown active) for {contract_address}"
                    )
                    high_alert_count += 1
                    continue

                job_compat = {
                    "id":              job_id,
                    "app_id":          0,
                    "account_address": contract_address,
                    "alert_email":     alert_email if alert_email else None,
                    "telegram_chat_id": telegram_chat_id if telegram_chat_id else None,
                }
                await dispatch_alerts(job_compat, result, txn)
                _set_cooldown(contract_address)
                high_alert_count += 1

        if high_alert_count:
            logger.warning(
                f"[Monitor] {high_alert_count} HIGH alert(s) processed for {contract_address}"
            )

        # 5. Update last seen round
        highest_round = get_highest_round(new_txns, last_txn)
        if highest_round > last_txn:
            await asyncio.to_thread(
                lambda: supabase.table("monitored_contracts").update(
                    {"last_txn": highest_round + 1}
                ).eq("id", job_id).execute()
            )

    except Exception as e:
        logger.error(f"[Monitor] Error processing job {job_id}: {e}", exc_info=True)


async def run_monitoring_cycle():
    """
    Core monitoring cycle — called every 30s by MonitoringManager.
    Fetches all active contracts and processes them concurrently.
    """
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("monitored_contracts")
            .select("*")
            .eq("status", "active")
            .execute()
        )
        active_jobs = response.data
        if not active_jobs:
            logger.debug("[Monitor] No active monitoring jobs.")
            return

        logger.info(f"[Monitor] Cycle — {len(active_jobs)} active job(s)")
        tasks = [process_monitoring_job(job) for job in active_jobs]
        await asyncio.gather(*tasks, return_exceptions=True)

    except Exception as e:
        logger.error(f"[Monitor] Cycle error: {e}", exc_info=True)
