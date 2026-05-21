# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import create_indexes
from services.monitor_service import start_scheduler, shutdown_scheduler
from routes import scan, certificates, monitor, contracts

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await create_indexes()
        start_scheduler()
        print("AlgoShield AI backend started")
    except Exception as e:
        print(f"ERROR: Backend initialization failed (is MongoDB running?): {e}")
    yield
    # Shutdown
    try:
        shutdown_scheduler()
    except:
        pass
    print("AlgoShield backend stopped")

app = FastAPI(
    title="AlgoShield AI API",
    version="1.0.0",
    description="Algorand smart contract security platform",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router,         prefix="/api", tags=["Scan"])
app.include_router(certificates.router, prefix="/api", tags=["Certificates"])
app.include_router(monitor.router,      prefix="/api", tags=["Monitor"])
app.include_router(contracts.router,    prefix="/api", tags=["Contracts"])

@app.get("/health")
def health_check():
    return {"status": "AlgoShield AI is running", "version": "1.0.0"}

@app.post("/analyze")
async def analyze_contract(
    wallet_address: str = Form(...),
    file: UploadFile = File(None),
    app_id: int = Form(None)
):
    """Direct /analyze endpoint for frontend compatibility"""
    from scanner import scan_contract as ai_scan
    from algorand_fetcher import fetch_contract_by_app_id
    
    if file:
        contract_code = (await file.read()).decode("utf-8")
    elif app_id:
        try:
            fetched = fetch_contract_by_app_id(app_id, use_mainnet=True)
            contract_code = fetched["approval_program"]
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Could not fetch App ID {app_id}: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Provide either a file upload or an app_id")
    
    if not contract_code or not contract_code.strip():
        raise HTTPException(status_code=400, detail="Contract code is empty")
    
    result = ai_scan(contract_code)
    return result
