# models.py
from datetime import datetime
import uuid

def new_scan_doc(
    wallet_address: str,
    contract_code: str,
    contract_hash: str,
    score: int,
    risk_level: str,
    vulnerabilities: list,
    summary: str = "",
    app_id: int = None,
    contract_filename: str = None
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "wallet_address": wallet_address,
        "app_id": app_id,
        "contract_filename": contract_filename,
        "contract_code": contract_code,
        "contract_hash": contract_hash,
        "score": score,
        "risk_level": risk_level,          # "Critical" | "Risky" | "Safe"
        "vulnerabilities": vulnerabilities, # list of dicts from AI scanner
        "summary": summary,
        "created_at": datetime.utcnow()
    }


def new_certificate_doc(
    scan_id: str,
    wallet_address: str,
    score: int,
    asset_id: int,
    txn_id: str,
    explorer_url: str,
    app_id: int = None
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "scan_id": scan_id,
        "wallet_address": wallet_address,
        "app_id": app_id,
        "asset_id": asset_id,              # Algorand ASA ID of the minted NFT
        "txn_id": txn_id,                  # Algorand transaction ID
        "explorer_url": explorer_url,
        "score": score,
        "created_at": datetime.utcnow()
    }


def new_monitor_job_doc(
    wallet_address: str,
    app_id: int,
    account_address: str,
    telegram_chat_id: str = None,
    alert_email: str = None
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "wallet_address": wallet_address,
        "app_id": app_id,
        "account_address": account_address,
        "is_active": True,
        "telegram_chat_id": telegram_chat_id,
        "alert_email": alert_email,
        "last_txn_id": None,               # ID of last processed transaction
        "created_at": datetime.utcnow()
    }


def new_alert_doc(
    monitor_job_id: str,
    app_id: int,
    anomaly_score: float,
    severity: str,
    description: str,
    txn_id: str = None
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "monitor_job_id": monitor_job_id,
        "app_id": app_id,
        "txn_id": txn_id,
        "anomaly_score": anomaly_score,
        "severity": severity,              # "Critical" | "High" | "Medium" | "Low"
        "description": description,
        "is_read": False,
        "created_at": datetime.utcnow()
    }
