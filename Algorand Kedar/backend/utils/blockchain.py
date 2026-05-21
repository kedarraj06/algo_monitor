import os
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Primary: use env var. Fallback to algonode.cloud if env var points to offline service.
_env_url = os.getenv("INDEXER_API_URL", "https://mainnet-idx.algonode.cloud")
INDEXER_API_URL = _env_url if _env_url else "https://mainnet-idx.algonode.cloud"

async def fetch_contract_transactions(contract_address: str, min_round: int = 0) -> list:
    """
    Fetches transactions for a given Algorand contract address.
    If min_round is provided, fetches only transactions that occurred at or after this round.
    """
    if not contract_address or not isinstance(contract_address, str):
        logger.error("Invalid contract address provided.")
        raise ValueError("Invalid contract address.")

    # Note: Algorand indexer uses base32 addresses for accounts, or application IDs.
    # The prompt specified GET /v2/accounts/{address}/transactions
    url = f"{INDEXER_API_URL}/v2/accounts/{contract_address}/transactions"
    
    params = {"limit": 100}  # Fetch up to 100 transactions per request
    if min_round > 0:
        # min-round filters to only transactions CONFIRMED at or after this round
        params["min-round"] = min_round

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 400:
                logger.error(f"Bad Request: Invalid address {contract_address}.")
                return []
            elif response.status_code != 200:
                logger.error(f"Indexer API returned status {response.status_code} for address {contract_address}.")
                response.raise_for_status()
                
            data = response.json()
            transactions = data.get("transactions", [])
            
            if not transactions:
                logger.info(f"No transactions found for address {contract_address} (min_round={min_round}).")
            else:
                logger.info(f"Fetched {len(transactions)} transactions for address {contract_address} (min_round={min_round}).")
                
            return transactions
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching transactions: {e}")
        return []
    except httpx.RequestError as e:
        logger.error(f"Request error occurred while fetching transactions: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
