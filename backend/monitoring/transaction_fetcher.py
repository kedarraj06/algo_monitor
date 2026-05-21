# backend/monitoring/transaction_fetcher.py
import logging
from typing import List, Dict, Any
from utils.blockchain_indexer import fetch_contract_transactions

logger = logging.getLogger(__name__)

async def fetch_new_transactions(account_address: str, last_round: int) -> List[Dict[str, Any]]:
    """
    Fetches new transactions for a contract since the last round.
    """
    try:
        new_txns = await fetch_contract_transactions(
            contract_address=account_address,
            min_round=last_round
        )
        return new_txns
    except Exception as e:
        logger.error(f"Error fetching transactions for {account_address}: {e}")
        return []

def get_highest_round(txns: List[Dict[str, Any]], current_last_round: int) -> int:
    """
    Finds the highest confirmed round among the fetched transactions.
    """
    highest = current_last_round
    for txn in txns:
        rnd = txn.get("confirmed-round", 0)
        if rnd > highest:
            highest = rnd
    return highest
