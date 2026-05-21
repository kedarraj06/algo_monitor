# backend/verify_indexer_baseline.py
import asyncio
import logging
from utils.blockchain_indexer import fetch_contract_transactions
from monitoring.risk_engine import evaluate_contract_baseline

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("baseline_verifier")

async def main():
    print("=" * 60)
    print("  AlgoShield AI — Real Mainnet Baseline Scan Verification")
    print("=" * 60)

    # 1. Test a real mainnet Application ID
    # App ID 971350278 is the Folks Finance Pool Manager App on Mainnet
    app_id = "971350278"
    logger.info(f"Initiating baseline scan for Mainnet Application ID: {app_id}")
    app_txns = await fetch_contract_transactions(app_id, min_round=0)
    logger.info(f"Retrieved {len(app_txns)} transactions for App {app_id}")
    
    app_severity, app_explanation, app_score = evaluate_contract_baseline(app_id, app_txns)
    print(f"\n[App ID {app_id} Scan Results]")
    print(f"Status      : {app_severity}")
    print(f"Risk Score  : {app_score:.3f}")
    print(f"Explanation : {app_explanation}")
    print("-" * 60)

    # 2. Test a highly active mainnet Account Address
    # Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA is the official Algorand FeeSink
    real_addr = "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA"
    logger.info(f"Initiating baseline scan for Mainnet Account Address: {real_addr}")
    acc_txns = await fetch_contract_transactions(real_addr, min_round=0)
    logger.info(f"Retrieved {len(acc_txns)} transactions for Address {real_addr}")
    
    acc_severity, acc_explanation, acc_score = evaluate_contract_baseline(real_addr, acc_txns)
    print(f"\n[Account {real_addr[:12]}... Scan Results]")
    print(f"Status      : {acc_severity}")
    print(f"Risk Score  : {acc_score:.3f}")
    print(f"Explanation : {acc_explanation}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
