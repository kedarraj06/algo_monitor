# backend/blockchain/nft_minter.py
import json, os, hashlib
from datetime import datetime
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import AssetConfigTxn, AssetTransferTxn, wait_for_confirmation
from dotenv import load_dotenv
load_dotenv()

ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"
ALGOD_TOKEN   = ""

def _client():
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS, headers={"User-Agent": "AlgoShield/1.0"})

def mint_security_certificate(recipient_address: str, app_id: int, security_score: int, scan_id: str, contract_hash: str) -> dict:
    phrase = os.getenv("PLATFORM_MNEMONIC", "")
    if not phrase or phrase == "word1 word2 word3 ... word25":
        raise ValueError("PLATFORM_MNEMONIC not set in .env. Run generate_wallet.py first.")

    private_key    = mnemonic.to_private_key(phrase)
    platform_addr  = account.address_from_private_key(private_key)
    client         = _client()
    params         = client.suggested_params()
    short_hash     = contract_hash[:8].upper()

    arc69_metadata = {
        "standard": "arc69",
        "description": f"AlgoShield AI Security Certificate — Contract {short_hash}",
        "external_url": f"https://algoshield.io/certificates/{scan_id}",
        "mime_type": "image/png",
        "properties": {
            "app_id": str(app_id),
            "security_score": security_score,
            "risk_level": "Safe",
            "contract_hash": contract_hash,
            "audit_date": datetime.utcnow().isoformat(),
            "scan_id": scan_id,
            "audited_by": "AlgoShield AI v2.0"
        }
    }

    # Create NFT (ASA with total=1)
    create_txn = AssetConfigTxn(
        sender=platform_addr, sp=params, total=1, decimals=0,
        default_frozen=False,
        unit_name="SHIELD",
        asset_name=f"AlgoShield Cert #{short_hash}",
        manager=platform_addr, reserve=platform_addr,
        freeze=platform_addr, clawback=platform_addr,
        url="https://algoshield.io/nft/",
        note=json.dumps(arc69_metadata).encode()
    )
    signed_create = create_txn.sign(private_key)
    create_txn_id = client.send_transaction(signed_create)
    confirmed     = wait_for_confirmation(client, create_txn_id, wait_rounds=4)
    asset_id      = confirmed["asset-index"]

    # Transfer to recipient (they must opt-in first — for demo, send to platform if opt-in fails)
    try:
        transfer_txn = AssetTransferTxn(
            sender=platform_addr, sp=params,
            receiver=recipient_address, amt=1, index=asset_id
        )
        signed_transfer = transfer_txn.sign(private_key)
        transfer_txn_id = client.send_transaction(signed_transfer)
        wait_for_confirmation(client, transfer_txn_id, wait_rounds=4)
    except Exception:
        transfer_txn_id = create_txn_id  # keep in platform wallet if recipient not opted in

    return {
        "asset_id":     asset_id,
        "txn_id":       create_txn_id,
        "explorer_url": f"https://testnet.explorer.perawallet.app/asset/{asset_id}",
        "metadata":     arc69_metadata
    }

def compute_contract_hash(contract_code: str) -> str:
    return hashlib.sha256(contract_code.encode()).hexdigest()
