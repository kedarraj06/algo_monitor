# backend/monitoring/alert_manager.py
"""
Alert Manager — Async multi-channel notification dispatcher
===========================================================
Only dispatches Telegram/Email for HIGH severity alerts.
Runs blocking I/O (SMTP, requests) in thread executors.
"""
import logging
import asyncio
from typing import Dict, Any

from utils.email_service import send_alert_email
from utils.telegram_service import send_telegram_alert

logger = logging.getLogger(__name__)


async def dispatch_alerts(job: Dict[str, Any], result: Dict[str, Any], txn: Dict[str, Any]):
    """
    Dispatch external notifications for a HIGH severity alert.
    Silently no-ops for non-HIGH results.
    Runs SMTP/Telegram in background threads to avoid blocking event loop.
    """
    severity = result.get("severity", "SAFE")

    # Guard: only dispatch for HIGH risk
    if severity != "HIGH":
        logger.debug(f"[AlertManager] Skipping dispatch for severity={severity}")
        return

    unified = {
        "severity":     severity,
        "description":  result.get("description", "Suspicious activity detected"),
        "anomaly_score":result.get("anomaly_score", 0.0),
        "label":        result.get("ai_label", "UNKNOWN"),
        "risk_level":   result.get("ai_risk_level", "HIGH"),
    }

    tasks = []

    if job.get("telegram_chat_id"):
        tasks.append(asyncio.to_thread(
            send_telegram_alert,
            job["telegram_chat_id"],
            job.get("account_address", ""),
            unified
        ))

    if job.get("alert_email"):
        tasks.append(asyncio.to_thread(
            send_alert_email,
            to_email=job["alert_email"],
            contract_address=job.get("account_address", ""),
            txn_id=txn.get("id", "Unknown"),
            txn_type=txn.get("tx-type", "pay"),
            risk_level=severity,
            label=unified["label"]
        ))

    if not tasks:
        logger.debug("[AlertManager] No alert channels configured for this job.")
        return

    # Run concurrently in thread pool, capture exceptions without crashing
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            logger.error(f"[AlertManager] Channel {i} failed: {res}")

