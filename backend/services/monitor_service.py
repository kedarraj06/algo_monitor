# services/monitor_service.py
import os
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
try:
    from utils.blockchain_indexer import fetch_contract_transactions
    from utils.email_service import send_alert_email
    from utils.telegram_service import send_telegram_alert
    from ml_models.anomaly import get_monitor
    from utils.ai_analyzer import analyze_transaction
    from utils.supabase_client import get_supabase_client
except ImportError:
    pass
from dotenv import load_dotenv

load_dotenv()

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            run_monitoring_cycle,
            trigger='interval',
            seconds=30,
            id='monitor_cycle',
            replace_existing=True
        )
        scheduler.start()
        print("✅ AlgoShield monitoring scheduler started (every 30s)")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("Scheduler stopped")

def run_monitoring_cycle():
    """
    Called every 30 seconds by APScheduler.
    Fetches new transactions for each active monitor job,
    runs BOTH anomaly detection (Isolation Forest) AND AI classification (Random Forest),
    saves alerts, sends Email + Telegram messages.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    supabase = get_supabase_client()

    response = supabase.table("monitored_contracts").select("*").eq("is_active", True).execute()
    active_jobs = response.data

    if not active_jobs:
        return

    for job in active_jobs:
        job_id = job["id"]

        try:
            # 1. Fetch new transactions from Algorand Indexer
            new_txns = loop.run_until_complete(fetch_contract_transactions(
                contract_address=job["account_address"],
                min_round=job.get("last_round", 0)
            ))

            if not new_txns:
                continue

            # 2. Update the last seen round based on highest confirmed-round in new txns
            highest_round = job.get("last_round", 0) or 0
            for txn in new_txns:
                rnd = txn.get("confirmed-round", 0)
                if rnd > highest_round:
                    highest_round = rnd

            supabase.table("monitored_contracts").update(
                {"last_round": highest_round + 1}
            ).eq("id", job_id).execute()

            # 3. Get the Isolation Forest anomaly detector
            ai_monitor = get_monitor(str(job["app_id"]))
            ai_monitor.add_transactions(new_txns)

            # 4. Check each new transaction with BOTH models
            for txn in new_txns:
                # Model 1: Isolation Forest anomaly detection
                anomaly_result = ai_monitor.check_transaction(txn)

                # Model 2: Random Forest AI classification
                ai_result = analyze_transaction(txn)

                # Alert if EITHER model flags the transaction
                should_alert = anomaly_result.get("is_anomaly") or ai_result.get("is_risky")

                if should_alert:
                    # Combine scores from both models for richer alert data
                    combined_severity = anomaly_result.get("severity", "Medium")
                    if ai_result.get("is_risky"):
                        # AI classification takes priority for severity
                        combined_severity = ai_result.get("risk_level", "MEDIUM")

                    alert_doc = {
                        "monitor_job_id": job_id,
                        "app_id":         job["app_id"],
                        "txn_id":         txn.get("id"),
                        "anomaly_score":  anomaly_result.get("anomaly_score", 0.0),
                        "ai_label":       ai_result.get("label", "UNKNOWN"),
                        "ai_risk_level":  ai_result.get("risk_level", "UNKNOWN"),
                        "severity":       combined_severity,
                        "description":    anomaly_result.get("description") or ai_result.get("error", "Unknown"),
                        "is_read":        False
                    }
                    supabase.table("alerts").insert(alert_doc).execute()

                    print(f"🚨 Alert — App {job['app_id']} | {combined_severity} | {alert_doc['description']}")

                    # Build a unified result dict for alert channels
                    unified_result = {
                        "severity": combined_severity,
                        "description": alert_doc["description"],
                        "anomaly_score": anomaly_result.get("anomaly_score", 0.0),
                        "label": ai_result.get("label", "UNKNOWN"),
                        "risk_level": ai_result.get("risk_level", "UNKNOWN"),
                        "prediction": ai_result.get("prediction", -1),
                    }

                    # 5. Send Telegram notification if configured
                    if job.get("telegram_chat_id"):
                        try:
                            send_telegram_alert(job["telegram_chat_id"], job["app_id"], unified_result)
                        except Exception as e:
                            print(f"⚠️ Telegram alert failed: {e}")

                    # 6. Send Email notification if configured
                    if job.get("alert_email"):
                        try:
                            send_alert_email(
                                to_email=job["alert_email"],
                                contract_address=job["account_address"],
                                txn_id=txn.get("id", "Unknown"),
                                txn_type=txn.get("tx-type", "Unknown"),
                                risk_level=combined_severity,
                                label=ai_result.get("label", anomaly_result.get("description", "Unknown"))
                            )
                        except Exception as e:
                            print(f"⚠️ Email alert failed: {e}")

        except Exception as e:
            print(f"Error in monitor job {job_id}: {e}")
