# routes/contracts.py
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/contracts/{app_id}")
def get_contract(app_id: int, mainnet: bool = True):
    """
    Fetch a deployed Algorand smart contract's TEAL code by App ID.
    Used when developer enters an App ID instead of uploading a file.
    """
    try:
        from algorand_fetcher import fetch_contract_by_app_id
        result = fetch_contract_by_app_id(app_id, use_mainnet=mainnet)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch contract: {str(e)}")
