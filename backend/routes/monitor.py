# routes/monitor.py
"""
Monitoring API Routes
=====================
Route registration ORDER matters in FastAPI:
  - Static paths must come BEFORE parameterized paths.
  - /monitor/list and /monitor/jobs/{x} must be ABOVE /monitor/{app_id}/alerts
    because FastAPI matches top-to-bottom and {app_id} would capture "list".

Supabase schema used:
  monitored_contracts: id, contract_address, email, status, last_txn, created_at
  alerts:              id, contract_address, message, risk_level, timestamp
"""
import re
import logging
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from utils.supabase_client import get_supabase_client
from monitoring.monitoring_manager import manager

router = APIRouter(tags=["monitoring"])
logger = logging.getLogger(__name__)

# ── Algorand address validation ─────────────────────────────────────────────
# Real Algorand addresses are 58-char base32 strings.
# App IDs are numeric only. We accept both for account_address field.
_ALGO_ADDR_RE = re.compile(r'^[A-Z2-7]{58}$')
_NUMERIC_RE = re.compile(r'^\d+$')

def _is_valid_address(addr: str) -> bool:
    """Accept real Algorand account addresses or numeric app IDs."""
    if not addr:
        return False
    return bool(_ALGO_ADDR_RE.match(addr)) or bool(_NUMERIC_RE.match(addr))

def _is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', email)) if email else True


# ── Request schema ───────────────────────────────────────────────────────────
class StartMonitorRequest(BaseModel):
    wallet_address: str
    app_id: int
    account_address: str          # Algorand account addr OR numeric app ID
    telegram_chat_id: Optional[str] = None
    alert_email: Optional[str] = None

    @validator("app_id")
    def validate_app_id(cls, v):
        if v < 0:
            raise ValueError("app_id must be non-negative")
        return v

    @validator("alert_email")
    def validate_email(cls, v):
        if v and not _is_valid_email(v):
            raise ValueError(f"Invalid email address: {v}")
        return v


# ══════════════════════════════════════════════════════════════════════════════
# IMPORTANT: Register static routes FIRST to avoid {app_id} capturing "list"
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/monitor/list")
async def list_monitored_contracts():
    """List all monitored contracts (static path — must come first)."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("monitored_contracts").select("*").execute()
        return {"contracts": response.data}
    except Exception as e:
        logger.error(f"[Monitor] list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/jobs/{wallet_address}")
async def get_monitor_jobs(wallet_address: str):
    """Get all monitor jobs for UI display."""
    try:
        supabase = get_supabase_client()
        res = supabase.table("monitored_contracts").select("*").execute()
        return [
            {
                "job_id":          job["id"],
                "app_id":          0,
                "account_address": job["contract_address"],
                "is_active":       job["status"] == "active",
                "created_at":      job["created_at"],
            }
            for job in res.data
        ]
    except Exception as e:
        logger.error(f"[Monitor] jobs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── WebSocket — must be registered before parameterized GET routes ───────────
@router.websocket("/monitor/ws/{app_id}")
async def websocket_monitor_endpoint(websocket: WebSocket, app_id: int):
    """WebSocket endpoint — real-time monitoring feed."""
    await manager.connect(app_id, websocket)
    logger.info(f"[WS] Client connected for app_id={app_id}")
    try:
        while True:
            # Keep connection alive; client sends pings if it needs to
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(app_id, websocket)
        logger.info(f"[WS] Client disconnected from app_id={app_id}")


# ── POST /monitor/start ──────────────────────────────────────────────────────
@router.post("/monitor/start")
async def start_monitoring(req: StartMonitorRequest):
    """
    Register a contract address for 24/7 async monitoring.

    Validation:
      - app_id must be >= 0
      - account_address must be a real 58-char Algorand address or numeric ID
      - alert_email must be a valid email format if provided
    """
    import asyncio
    # Validate address format — prevent junk from reaching the Algorand indexer
    addr = req.account_address.strip()
    if addr and not _is_valid_address(addr):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid account_address '{addr}'. "
                "Must be a 58-character Algorand account address (base32) "
                "or a numeric application ID."
            )
        )

    # If empty address was provided, derive a placeholder from app_id
    if not addr:
        addr = str(req.app_id)

    try:
        supabase = get_supabase_client()

        # ── 1. Immediate Initial Baseline Scan ──────────────────────────────
        from utils.blockchain_indexer import fetch_contract_transactions
        from monitoring.risk_engine import evaluate_contract_baseline

        logger.info(f"[Monitor] Running initial baseline scan for {addr}...")
        try:
            txns = await fetch_contract_transactions(addr, min_round=0)
            
            # Determine highest confirmed round
            highest_round = 0
            for txn in txns:
                rnd = txn.get("confirmed-round", 0)
                if rnd > highest_round:
                    highest_round = rnd

            # Evaluate initial baseline security health
            initial_severity, explanation, score = evaluate_contract_baseline(addr, txns)
        except Exception as scan_err:
            logger.error(f"[Monitor] Baseline scan failed for {addr}: {scan_err}")
            initial_severity = "ERROR"
            explanation = f"Could not connect to indexer or scan baseline: {str(scan_err)}"
            score = 0.0
            highest_round = 0
            txns = []

        # ── 2. Insert or update the monitoring job ──────────────────────────
        # Since contract_address has a unique constraint, we must update if it already exists
        email_val = f"{req.alert_email or ''}##{req.telegram_chat_id or ''}##{req.app_id}"
        
        existing = (
            supabase.table("monitored_contracts")
            .select("*")
            .eq("contract_address", addr)
            .execute()
        )
        
        if existing.data:
            row = existing.data[0]
            logger.info(f"[Monitor] Contract {addr} already exists in database (job={row['id'][:8]}...). Updating settings.")
            update_data = {
                "email":            email_val,
                "status":           "active",
                "last_txn":         highest_round + 1,
            }
            res = (
                supabase.table("monitored_contracts")
                .update(update_data)
                .eq("id", row["id"])
                .execute()
            )
            job_id = row["id"]
        else:
            insert_data = {
                "contract_address": addr,
                "email":            email_val,
                "status":           "active",
                "last_txn":         highest_round + 1,
            }
            res = supabase.table("monitored_contracts").insert(insert_data).execute()
            if not res.data:
                raise HTTPException(status_code=500, detail="Failed to insert monitor job into database")
            job_id = res.data[0]["id"]
            
        logger.info(f"[Monitor] Started monitoring {addr} (job={job_id[:8]}...) | Initial: {initial_severity}")

        # ── 3. Write initial scan alert to feed ─────────────────────────────
        initial_msg = f"Monitoring Started — {initial_severity}: {explanation}"
        alert_row = {
            "contract_address": addr,
            "message":          initial_msg,
            "risk_level":       initial_severity,
            "timestamp":        datetime.utcnow().isoformat(),
        }
        supabase.table("alerts").insert(alert_row).execute()

        # ── 4. Dispatch immediate Telegram & Email alerts ──────────────────
        if req.telegram_chat_id:
            try:
                from utils.telegram_service import send_telegram_alert
                unified_res = {
                    "severity":      initial_severity,
                    "description":   f"AlgoShield Live Monitoring Started!\nStatus: {initial_severity}\nDetails: {explanation}",
                    "anomaly_score": score,
                    "label":         initial_severity,
                    "risk_level":    initial_severity,
                }
                # Dispatched in separate thread to prevent blocking
                await asyncio.to_thread(
                    send_telegram_alert,
                    req.telegram_chat_id,
                    addr,
                    unified_res
                )
                logger.info(f"[Monitor] Baseline Telegram alert dispatched to {req.telegram_chat_id}")
            except Exception as te:
                logger.error(f"[Monitor] Telegram baseline notify failed: {te}")

        if req.alert_email:
            try:
                from utils.email_service import send_alert_email
                await asyncio.to_thread(
                    send_alert_email,
                    to_email=req.alert_email,
                    contract_address=addr,
                    txn_id="N/A (Baseline Scan)",
                    txn_type="Initial Audit",
                    risk_level=initial_severity,
                    label=explanation
                )
                logger.info(f"[Monitor] Baseline Email alert dispatched to {req.alert_email}")
            except Exception as ee:
                logger.error(f"[Monitor] Email baseline notify failed: {ee}")

        return {
            "job_id":    job_id,
            "message":   "Monitoring started successfully with initial baseline analysis",
            "is_active": True,
            "initial_status": initial_severity,
            "explanation": explanation
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Monitor] start error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ── POST /monitor/stop/{job_id} ──────────────────────────────────────────────
@router.post("/monitor/stop/{job_id}")
async def stop_monitoring(job_id: str):
    """Stop a monitoring job by setting status = 'inactive'."""
    try:
        supabase = get_supabase_client()
        res = (
            supabase.table("monitored_contracts")
            .update({"status": "inactive"})
            .eq("id", job_id)
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail=f"Monitor job {job_id} not found")
        logger.info(f"[Monitor] Stopped job {job_id[:8]}...")
        return {"message": "Monitoring stopped", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Monitor] stop error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /monitor/{app_id}/alerts — MUST come AFTER static routes ─────────────
@router.get("/monitor/{app_id}/alerts")
async def get_alerts(app_id: str, wallet_address: str):
    """
    Get the latest alerts for all active monitoring jobs.
    NOTE: app_id is matched against contract_address or job_app_id from the email field.
    """
    try:
        supabase = get_supabase_client()

        job_res = (
            supabase.table("monitored_contracts")
            .select("*")
            .eq("status", "active")
            .execute()
        )
        if not job_res.data:
            return {"job_id": None, "is_active": False, "app_id": app_id, "alerts": []}

        # Find the correct job among active ones
        job = None
        for r in job_res.data:
            c_addr = r.get("contract_address", "")
            job_email = r.get("email", "") or ""
            job_app_id = ""
            if "##" in job_email:
                parts = job_email.split("##")
                if len(parts) > 2:
                    job_app_id = parts[2]
            
            # Match either contract_address or parsed app_id or UUID
            if c_addr == app_id or job_app_id == app_id or r.get("id") == app_id:
                job = r
                break
        
        # Fallback for compatibility: if not found, use the first active job
        if not job:
            job = job_res.data[0]

        alerts_res = (
            supabase.table("alerts")
            .select("*")
            .eq("contract_address", job["contract_address"])
            .order("timestamp", desc=True)
            .limit(20)
            .execute()
        )

        alert_list = [
            {
                "id":            a["id"],
                "severity":      a.get("risk_level", "SAFE"),
                "description":   a.get("message", ""),
                "anomaly_score": 0.0,
                "txn_id":        None,
                "is_read":       False,
                "timestamp":     a.get("timestamp", datetime.utcnow().isoformat()),
            }
            for a in alerts_res.data
        ]

        return {
            "job_id":    job["id"],
            "is_active": job["status"] == "active",
            "app_id":    app_id,
            "alerts":    alert_list,
        }

    except Exception as e:
        logger.error(f"[Monitor] alerts fetch error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
