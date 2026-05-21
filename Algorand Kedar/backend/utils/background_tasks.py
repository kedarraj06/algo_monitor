"""
background_tasks.py
--------------------
Asynchronous background monitoring loop for AlgoShield AI.

Responsibilities:
  1. Every 30 seconds, query Supabase for all 'active' contracts
  2. For each contract, fetch new transactions from Algorand Indexer
     using last_txn (confirmed round) to avoid reprocessing
  3. Analyze each transaction using the existing ML pipeline (via ai_analyzer)
  4. If the transaction is flagged RISKY or SUSPICIOUS, insert an alert into DB
  5. Update last_txn in the database to the highest confirmed-round seen

Phase 5 additions: AI analysis + alert storage.
Phase 6 (email alerts) will be added next.
"""

import asyncio
import logging
from datetime import datetime, timezone

from utils.supabase_client import get_supabase_client
from utils.blockchain import fetch_contract_transactions
from utils.ai_analyzer import analyze_transaction
from utils.email_service import send_alert_email

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30


async def monitoring_loop():
    """
    Infinite async loop that monitors all active contracts every 30 seconds.
    Runs in the background without blocking the main FastAPI server.
    """
    logger.info("[Monitor] Background monitoring loop started.")

    while True:
        try:
            await _run_monitoring_cycle()
        except asyncio.CancelledError:
            logger.info("[Monitor] Monitoring loop cancelled. Shutting down.")
            break
        except Exception as e:
            logger.error(f"[Monitor] Unexpected error in monitoring cycle: {e}")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def _run_monitoring_cycle():
    """
    A single monitoring cycle:
    - Fetches all active contracts from Supabase
    - For each contract, fetches new transactions using last_txn as min_round
    - Analyzes each transaction with the AI pipeline
    - Stores alerts in DB for risky transactions
    - Updates last_txn in DB
    """
    supabase = get_supabase_client()

    # Step 1: Get all active contracts
    response = supabase.table("monitored_contracts").select("*").eq("status", "active").execute()
    contracts = response.data

    if not contracts:
        logger.info("[Monitor] No active contracts to monitor.")
        return

    logger.info(f"[Monitor] Checking {len(contracts)} active contract(s)...")

    for contract in contracts:
        address = contract["contract_address"]
        last_txn = contract.get("last_txn", 0) or 0
        email = contract.get("email", "")

        try:
            # Step 2: Fetch new transactions since last_txn round
            min_round = last_txn + 1 if last_txn > 0 else 0
            transactions = await fetch_contract_transactions(address, min_round=min_round)

            if not transactions:
                logger.info(f"[Monitor] [{address[:12]}...] No new transactions since round {last_txn}.")
                continue

            logger.info(f"[Monitor] [{address[:12]}...] Found {len(transactions)} new transaction(s). Analyzing...")

            max_round = 0

            for txn in transactions:
                txn_id = txn.get("id", "N/A")
                txn_type = txn.get("tx-type", "N/A")
                round_num = txn.get("confirmed-round", 0)

                # Step 3: Run AI analysis on this transaction
                # analyze_transaction is CPU-bound (ML model), run in thread pool
                result = await asyncio.to_thread(analyze_transaction, txn)

                label = result["label"]
                risk_level = result["risk_level"]
                error = result["error"]

                if error:
                    logger.warning(
                        f"[Monitor] [{address[:12]}...] TXN {txn_id} analysis error: {error}"
                    )
                else:
                    logger.info(
                        f"[Monitor] [{address[:12]}...] TXN {txn_id} | "
                        f"type={txn_type} | round={round_num} | "
                        f"label={label} | risk_level={risk_level}"
                    )

                # Step 4: Store alert + send email if transaction is flagged risky/suspicious
                if result["is_risky"]:
                    await _store_alert(supabase, address, txn_id, txn_type, label, risk_level, email)

                # Track highest confirmed-round seen in this batch
                if round_num > max_round:
                    max_round = round_num

            # Step 5: Update last_txn to the highest confirmed-round in this batch
            if max_round > last_txn:
                supabase.table("monitored_contracts").update(
                    {"last_txn": max_round}
                ).eq("contract_address", address).execute()
                logger.info(f"[Monitor] [{address[:12]}...] Updated last_txn to round {max_round}.")

        except Exception as e:
            logger.error(f"[Monitor] [{address[:12]}...] Error during monitoring: {e}")
            continue


async def _store_alert(supabase, address: str, txn_id: str, txn_type: str,
                       label: str, risk_level: str, email: str):
    """
    Insert a new alert row into the Supabase 'alerts' table.
    Then send an email notification to the contract owner.
    Called when the AI flags a transaction as RISKY or SUSPICIOUS.
    """
    try:
        message = (
            f"Suspicious transaction detected: TXN {txn_id} "
            f"(type={txn_type}) flagged as {label}."
        )
        alert_data = {
            "contract_address": address,
            "message": message,
            "risk_level": risk_level,
        }
        supabase.table("alerts").insert(alert_data).execute()
        logger.info(
            f"[Alert] Stored alert for [{address[:12]}...] | "
            f"TXN {txn_id} | risk_level={risk_level}"
        )
    except Exception as e:
        logger.error(f"[Alert] Failed to store alert for [{address[:12]}...]: {e}")
        return  # Don't send email if DB insert failed

    # Send email notification asynchronously (in thread pool to avoid blocking loop)
    try:
        sent = await asyncio.to_thread(
            send_alert_email,
            email,
            address,
            txn_id,
            txn_type,
            risk_level,
            label,
        )
        if sent:
            logger.info(f"[Email] Alert email dispatched to {email} for TXN {txn_id[:16]}...")
        else:
            logger.warning(f"[Email] Email not sent for TXN {txn_id[:16]}... (check logs above).")
    except Exception as e:
        logger.error(f"[Email] Unexpected failure dispatching email to {email}: {e}")
