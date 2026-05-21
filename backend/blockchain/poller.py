# backend/blockchain/poller.py
import requests

MAINNET_IDX = "https://mainnet-idx.algonode.cloud"
TESTNET_IDX = "https://testnet-idx.algonode.cloud"

def get_account_transactions(account_address: str, app_id: int = None, limit: int = 20, use_mainnet: bool = True) -> list:
    base = MAINNET_IDX if use_mainnet else TESTNET_IDX
    url  = f"{base}/v2/accounts/{account_address}/transactions"
    params = {"limit": limit}
    if app_id:
        params["application-id"] = app_id
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            return res.json().get("transactions", [])
    except Exception as e:
        print(f"[Poller] Error: {e}")
    return []

def poll_new_transactions(account_address: str, app_id: int = None, last_seen_txn_id: str = None) -> list:
    all_txns = get_account_transactions(account_address, app_id)
    if not last_seen_txn_id:
        return all_txns
    new_txns = []
    for txn in all_txns:
        if txn.get("id") == last_seen_txn_id:
            break
        new_txns.append(txn)
    return new_txns
