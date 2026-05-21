# schemas.py
from pydantic import BaseModel
from typing import Optional

class MintRequest(BaseModel):
    scan_id: str
    wallet_address: str

class StartMonitorRequest(BaseModel):
    wallet_address: str
    app_id: int
    account_address: str
    telegram_chat_id: Optional[str] = None
    alert_email: Optional[str] = None
