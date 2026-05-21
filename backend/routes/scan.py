# routes/scan.py
import hashlib
import uuid
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header, Depends
from database import scans_col, certificates_col
from models import new_scan_doc

router = APIRouter()

VALID_API_KEYS = {"demo-key-123", "hackathon-key-456"}

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key and x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@router.get("/health")
async def health():
    return {"status": "AlgoShield AI is running", "version": "1.0.0"}

@router.post("/analyze")
async def analyze_contract(
    wallet_address: str = Form(...),
    file: UploadFile = File(None),
    app_id: int = Form(None),
    api_key: str = Depends(verify_api_key)
):
    """
    Accepts either:
    - A .teal or .py file upload
    - An Algorand App ID (fetches real TEAL from mainnet)

    Returns the full security scan result.
    """
    # Step 1: Get the contract code
    if file:
        raw = await file.read()
        try:
            contract_code = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be a UTF-8 text file (.teal or .py)")
        contract_filename = file.filename

    elif app_id:
        try:
            from algorand_fetcher import fetch_contract_by_app_id
            fetched = fetch_contract_by_app_id(app_id, use_mainnet=True)
            contract_code = fetched["approval_program"]
            contract_filename = None
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Could not fetch App ID {app_id}: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail="Provide either a file upload or an app_id")

    if not contract_code or not contract_code.strip():
        raise HTTPException(status_code=400, detail="Contract code is empty")

    # Step 2: Run AI security scan
    try:
        from scanner import scan_contract as ai_scan
        scan_result = ai_scan(contract_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI scan failed: {str(e)}")

    # Step 3: Save result to MongoDB
    contract_hash = hashlib.sha256(contract_code.encode()).hexdigest()
    
    # Merge manual vulnerabilities and AI suggestions for the frontend
    all_vulns = scan_result.get("suggestions", [])
    if not all_vulns and scan_result.get("vulnerabilities"):
        all_vulns = scan_result.get("vulnerabilities")

    doc = new_scan_doc(
        wallet_address=wallet_address,
        contract_code=contract_code,
        contract_hash=contract_hash,
        score=int(scan_result["score"]),
        risk_level=scan_result["risk_level"],
        vulnerabilities=all_vulns,
        summary=scan_result.get("summary", ""),
        app_id=app_id,
        contract_filename=contract_filename
    )

    await scans_col.insert_one(doc)

    return {
        "scan_id":         doc["_id"],
        "score":           int(doc["score"]),
        "risk_level":      doc["risk_level"],
        "vulnerabilities": doc["vulnerabilities"],
        "summary":         doc["summary"],
        "slm_explanation": scan_result.get("slm_explanation"),
        "slm_suggestions": scan_result.get("slm_suggestions"),
        "contract_code":  contract_code,
        "contract_hash":  contract_hash
    }


@router.get("/scans/{wallet_address}")
async def get_scan_history(wallet_address: str):
    """Return last 10 scans for this wallet address."""
    cursor = scans_col.find(
        {"wallet_address": wallet_address},
        # Exclude the full contract_code from the list view (keep it small)
        {"contract_code": 0}
    ).sort("created_at", -1).limit(10)

    results = []
    async for doc in cursor:
        results.append({
            "scan_id":    doc["_id"],
            "score":      doc["score"],
            "risk_level": doc["risk_level"],
            "app_id":     doc.get("app_id"),
            "filename":   doc.get("contract_filename"),
            "created_at": doc["created_at"].isoformat()
        })

    return results


@router.get("/scan/{scan_id}")
async def get_scan(scan_id: str):
    """Get a single scan result by its ID."""
    doc = await scans_col.find_one({"_id": scan_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Scan not found")

    doc["scan_id"] = doc.pop("_id")
    doc["created_at"] = doc["created_at"].isoformat()
    return doc


@router.post("/analyze-with-slm")
async def analyze_with_slm(teal_code: str = Form(...)):
    """
    Use the Phi-3-mini SLM to analyze TEAL contract code.
    Returns detailed natural language explanation and suggestions.
    """
    try:
        from ml_models import slm_inference
        explanation = slm_inference.summarize_contract(teal_code[:3000])
        suggestions = slm_inference.suggest_improvements(teal_code[:3000], "assessed")
        return {"explanation": explanation, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SLM analysis failed: {str(e)}")

@router.post("/suggest")
async def get_suggestions(
    file: UploadFile = File(None),
    scan_id: str = Form(None),
    wallet_address: str = Form(default="anonymous")
):
    """
    Get AI-powered line-by-line fix suggestions for a TEAL contract.
    Accepts either a fresh file upload OR a scan_id to load from MongoDB.
    """
    # Get contract code
    if file:
        try:
            contract_code = (await file.read()).decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read file: {e}")
    elif scan_id:
        # Load from MongoDB using existing scan
        from database import scans_col
        scan = await scans_col.find_one({"_id": scan_id})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        contract_code = scan.get("contract_code", "")
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or scan_id")

    if not contract_code.strip():
        raise HTTPException(status_code=400, detail="Contract code is empty")

    try:
        from ml_models.suggester import get_suggestions as get_suggs
        result = get_suggs(contract_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion engine failed: {e}")


# ──────────────────────────────────────────────
# Certificate Minting & Details Endpoints
# ──────────────────────────────────────────────
class MintRequest(BaseModel):
    scan_id: str
    wallet_address: str


@router.post("/mint-certificate")
async def mint_certificate(req: MintRequest):
    scan = await scans_col.find_one({"_id": req.scan_id})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan["score"] < 70:
        raise HTTPException(status_code=400, detail=f"Score must be 70+ to mint. Current: {scan['score']}")
    if scan["wallet_address"] != req.wallet_address:
        raise HTTPException(status_code=403, detail="Wallet address mismatch")

    existing = await certificates_col.find_one({"scan_id": req.scan_id})
    if existing:
        existing["cert_id"] = existing.pop("_id")
        existing["created_at"] = existing["created_at"].isoformat()
        return {**existing, "message": "Already minted"}

    try:
        from blockchain.nft_minter import mint_security_certificate
        mint_result = mint_security_certificate(
            recipient_address=req.wallet_address,
            app_id=scan.get("app_id", 0) or 0,
            security_score=scan["score"],
            scan_id=req.scan_id,
            contract_hash=scan["contract_hash"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Minting failed: {e}")

    cert_id = str(uuid.uuid4())
    doc = {
        "_id": cert_id,
        "scan_id": req.scan_id,
        "wallet_address": req.wallet_address,
        "asset_id": mint_result["asset_id"],
        "txn_id": mint_result["txn_id"],
        "explorer_url": mint_result["explorer_url"],
        "score": scan["score"],
        "filename": scan.get("filename") or scan.get("contract_filename"),
        "created_at": datetime.utcnow()
    }
    await certificates_col.insert_one(doc)
    return {"cert_id": cert_id, **mint_result, "minted_at": doc["created_at"].isoformat()}


@router.get("/certificates/{wallet_address}")
async def get_certificates(wallet_address: str):
    cursor = certificates_col.find({"wallet_address": wallet_address}).sort("created_at", -1)
    results = []
    async for doc in cursor:
        results.append({
            "cert_id":      doc["_id"],
            "scan_id":      doc["scan_id"],
            "asset_id":     doc["asset_id"],
            "txn_id":       doc["txn_id"],
            "explorer_url": doc["explorer_url"],
            "score":        doc["score"],
            "filename":     doc.get("filename"),
            "minted_at":    doc["created_at"].isoformat()
        })
    return results
