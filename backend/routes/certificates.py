# routes/certificates.py
from fastapi import APIRouter, HTTPException
from schemas import MintRequest
from database import scans_col, certificates_col
from models import new_certificate_doc

router = APIRouter()

@router.post("/mint-certificate")
async def mint_certificate(req: MintRequest):
    """
    Mint an ARC-69 NFT certificate on Algorand for a scan that scored 70+.
    """
    # Get the scan from MongoDB
    scan = await scans_col.find_one({"_id": req.scan_id})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan["score"] < 70:
        raise HTTPException(
            status_code=400,
            detail=f"Score must be 70 or above to mint a certificate. Current score: {scan['score']}"
        )

    if scan["wallet_address"] != req.wallet_address:
        raise HTTPException(status_code=403, detail="Wallet address does not match the scan owner")

    # Check if certificate already minted for this scan
    existing = await certificates_col.find_one({"scan_id": req.scan_id})
    if existing:
        existing["cert_id"] = existing.pop("_id")
        existing["created_at"] = existing["created_at"].isoformat()
        return {**existing, "message": "Certificate already minted"}

    # Mint NFT on Algorand testnet
    try:
        from nft_minter import mint_security_certificate
        mint_result = mint_security_certificate(
            recipient_address=req.wallet_address,
            app_id=scan.get("app_id") or 0,
            security_score=scan["score"],
            scan_id=req.scan_id,
            contract_hash=scan["contract_hash"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NFT minting failed: {str(e)}")

    # Save certificate to MongoDB
    doc = new_certificate_doc(
        scan_id=req.scan_id,
        wallet_address=req.wallet_address,
        score=scan["score"],
        asset_id=mint_result["asset_id"],
        txn_id=mint_result["txn_id"],
        explorer_url=mint_result["explorer_url"],
        app_id=scan.get("app_id")
    )

    await certificates_col.insert_one(doc)

    return {
        "cert_id":      doc["_id"],
        "asset_id":     doc["asset_id"],
        "txn_id":       doc["txn_id"],
        "explorer_url": doc["explorer_url"],
        "score":        doc["score"],
        "minted_at":    doc["created_at"].isoformat()
    }


@router.get("/certificates/{wallet_address}")
async def get_certificates(wallet_address: str):
    """Return all NFT certificates for a wallet address."""
    cursor = certificates_col.find(
        {"wallet_address": wallet_address}
    ).sort("created_at", -1)

    results = []
    async for doc in cursor:
        results.append({
            "cert_id":      doc["_id"],
            "scan_id":      doc["scan_id"],
            "app_id":       doc.get("app_id"),
            "asset_id":     doc["asset_id"],
            "txn_id":       doc["txn_id"],
            "explorer_url": doc["explorer_url"],
            "score":        doc["score"],
            "minted_at":    doc["created_at"].isoformat()
        })

    return results
