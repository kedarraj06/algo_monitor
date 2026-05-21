from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from utils.supabase_client import get_supabase_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitor",
    tags=["Monitoring"]
)

class StartMonitorRequest(BaseModel):
    contract_address: str
    email: EmailStr

@router.post("/start")
async def start_monitoring(request: StartMonitorRequest):
    try:
        supabase = get_supabase_client()
        
        # Check if already monitored
        response = supabase.table("monitored_contracts").select("*").eq("contract_address", request.contract_address).execute()
        if len(response.data) > 0:
            raise HTTPException(status_code=400, detail="Contract is already being monitored.")
            
        # Insert new monitoring target
        insert_data = {
            "contract_address": request.contract_address,
            "email": request.email,
            "status": "active",
            "last_txn": 0
        }
        
        # Supabase Python client insert
        res = supabase.table("monitored_contracts").insert(insert_data).execute()
        
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to insert into database.")
            
        return {"message": "Monitoring started successfully", "data": res.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error starting monitoring: {error_msg}")
        if "duplicate key value violates unique constraint" in error_msg:
            raise HTTPException(status_code=400, detail="Contract is already being monitored.")
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")

@router.get("/list")
async def list_monitored_contracts():
    try:
        supabase = get_supabase_client()
        response = supabase.table("monitored_contracts").select("*").execute()
        return {"contracts": response.data}
    except Exception as e:
        logger.error(f"Error fetching monitored contracts: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/alerts")
async def get_alerts():
    try:
        supabase = get_supabase_client()
        response = supabase.table("alerts").select("*").execute()
        return {"alerts": response.data}
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
