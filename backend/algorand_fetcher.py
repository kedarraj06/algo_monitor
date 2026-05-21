# algorand_fetcher.py
import requests
import base64

TESTNET_INDEXER = "https://testnet-idx.algonode.cloud"
MAINNET_INDEXER = "https://mainnet-idx.algonode.cloud"

def fetch_contract_by_app_id(app_id: int, use_mainnet: bool = False) -> dict:
    """
    Fetch a deployed Algorand smart contract's TEAL code by its App ID.
    Returns the approval program and clear state program as readable strings.
    
    Args:
        app_id: The Algorand application ID (e.g., 811721471)
        use_mainnet: True = mainnet, False = testnet
    
    Returns:
        dict with approval_program, clear_program, global_state, creator
    """
    base_url = MAINNET_INDEXER if use_mainnet else TESTNET_INDEXER
    url = f"{base_url}/v2/applications/{app_id}"
    
    response = requests.get(url, timeout=10)
    
    if response.status_code == 404:
        raise ValueError(f"App ID {app_id} not found on {'mainnet' if use_mainnet else 'testnet'}")
    
    if response.status_code != 200:
        raise ConnectionError(f"Indexer returned status {response.status_code}")
    
    data = response.json()
    app = data.get("application", {})
    params = app.get("params", {})
    
    # The TEAL bytecode is base64-encoded in the response
    # Decode to bytes, then disassemble to readable TEAL
    approval_b64 = params.get("approval-program", "")
    clear_b64 = params.get("clear-state-program", "")
    
    approval_bytes = base64.b64decode(approval_b64) if approval_b64 else b""
    clear_bytes = base64.b64decode(clear_b64) if clear_b64 else b""
    
    # Try to disassemble bytecode to readable TEAL using algod
    approval_teal = disassemble_teal(approval_bytes)
    clear_teal = disassemble_teal(clear_bytes)
    
    return {
        "app_id": app_id,
        "creator": params.get("creator", ""),
        "approval_program": approval_teal,
        "clear_program": clear_teal,
        "global_state": params.get("global-state", []),
        "schema": {
            "global_ints": params.get("global-state-schema", {}).get("num-uint", 0),
            "global_bytes": params.get("global-state-schema", {}).get("num-byte-slice", 0),
        }
    }

def disassemble_teal(bytecode: bytes) -> str:
    """
    Disassemble TEAL bytecode back to human-readable TEAL source.
    Uses the Algod API endpoint for disassembly.
    """
    if not bytecode:
        return ""
    
    # Use AlgoNode's algod for disassembly
    algod_url = "https://testnet-api.algonode.cloud"
    
    try:
        response = requests.post(
            f"{algod_url}/v2/teal/disassemble",
            data=bytecode,
            headers={"Content-Type": "application/x-binary"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get("result", "")
    except Exception:
        pass
    
    # Fallback: return hex if disassembly fails
    return f"; Could not disassemble bytecode\n; Raw bytes: {bytecode.hex()[:200]}..."


def get_account_transactions(account_address: str, app_id: int = None, limit: int = 50) -> list:
    """
    Fetch recent transactions for an account, optionally filtered by app ID.
    Used by the monitoring system.
    
    Args:
        account_address: Algorand account address (e.g. "ABCDEF...XYZ")
        app_id: Optional - filter transactions by this application ID
        limit: Number of transactions to return
    
    Returns:
        List of transaction objects from Algorand Indexer
    """
    # Use Testnet indexer by default for development/hackathon as per prompt instructions
    url = f"{TESTNET_INDEXER}/v2/accounts/{account_address}/transactions"
    
    params = {"limit": limit}
    if app_id:
        params["application-id"] = app_id
    
    response = requests.get(url, params=params, timeout=15)
    
    if response.status_code != 200:
        return []
    
    return response.json().get("transactions", [])
