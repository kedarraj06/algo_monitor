# nft_minter.py
import json
import hashlib
import os
from datetime import datetime
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
from dotenv import load_dotenv

load_dotenv()

# AlgoNode free testnet - no API key needed
ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"
ALGOD_TOKEN = ""  # AlgoNode doesn't need a token

# ⚠️ IMPORTANT: This is the PLATFORM's wallet that mints the NFT
PLATFORM_MNEMONIC = os.getenv("PLATFORM_MNEMONIC")

def get_algod_client():
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS, headers={"User-Agent": "AlgoShield/1.0"})

def mint_security_certificate(
    recipient_address: str,
    app_id: int,
    security_score: int,
    scan_id: str,
    contract_hash: str
) -> dict:
    """
    Mint an ARC-69 NFT Security Certificate to the developer's wallet.
    
    Args:
        recipient_address: Developer's Pera Wallet address
        app_id: The Algorand App ID that was audited
        security_score: Score from 0-100
        scan_id: Unique ID of this scan (from our database)
        contract_hash: SHA256 hash of the contract code (proof of what was scanned)
    
    Returns:
        dict with asset_id, txn_id, explorer_url
    """
    client = get_algod_client()
    
    if not PLATFORM_MNEMONIC:
        raise ValueError("PLATFORM_MNEMONIC not set in .env")

    # Get platform private key from mnemonic
    private_key = mnemonic.to_private_key(PLATFORM_MNEMONIC)
    platform_address = account.address_from_private_key(private_key)
    
    # Build ARC-69 metadata (stored in transaction note)
    arc69_metadata = {
        "standard": "arc69",
        "description": f"AlgoShield AI Security Certificate for App ID {app_id}",
        "external_url": f"https://algoshield.io/certificates/{scan_id}",
        "mime_type": "image/png",
        "properties": {
            "app_id": str(app_id),
            "security_score": security_score,
            "risk_level": "Safe" if security_score >= 70 else "Risky",
            "contract_hash": contract_hash,
            "audit_date": datetime.utcnow().isoformat(),
            "scan_id": scan_id,
            "audited_by": "AlgoShield AI v1.0"
        }
    }
    
    # Get suggested transaction params
    params = client.suggested_params()
    
    # Generate a unique contract hash for naming
    short_hash = contract_hash[:8].upper()
    
    # Create Asset (NFT) — total=1 makes it a true NFT (non-fungible)
    txn = AssetConfigTxn(
        sender=platform_address,
        sp=params,
        total=1,                    # Only 1 exists = NFT
        decimals=0,                 # No decimals for NFT
        default_frozen=False,
        unit_name="SHIELD",         # Token symbol shown in wallets
        asset_name=f"AlgoShield Certificate #{short_hash}",
        manager=platform_address,
        reserve=platform_address,
        freeze=platform_address,
        clawback=platform_address,
        url="https://algoshield.io/nft/",  # NFT image URL (can be placeholder for demo)
        note=json.dumps(arc69_metadata).encode(),  # ARC-69 metadata in note field
    )
    
    # Sign with platform key
    signed_txn = txn.sign(private_key)
    
    # Submit to Algorand testnet
    txn_id = client.send_transaction(signed_txn)
    
    # Wait for confirmation (usually 1-2 blocks = ~4 seconds on Algorand)
    confirmed_txn = wait_for_confirmation(client, txn_id, wait_rounds=4)
    
    asset_id = confirmed_txn["asset-index"]
    
    # Now send the NFT from platform wallet to developer's wallet
    # (The AssetConfigTxn creates and gives NFT to sender, so we need to transfer it)
    try:
        transfer_txn_id = _transfer_nft_to_recipient(
            client, private_key, platform_address, 
            recipient_address, asset_id
        )
    except Exception as e:
        # Transfer might fail if recipient hasn't opted in
        print(f"NFT transfer failed (likely no opt-in): {e}")
        transfer_txn_id = None
    
    return {
        "asset_id": asset_id,
        "txn_id": txn_id,
        "transfer_txn_id": transfer_txn_id,
        "explorer_url": f"https://testnet.explorer.perawallet.app/asset/{asset_id}",
        "metadata": arc69_metadata
    }

def _transfer_nft_to_recipient(client, private_key, sender, recipient, asset_id):
    """Transfer the minted NFT to the developer's wallet."""
    from algosdk.transaction import AssetTransferTxn
    
    params = client.suggested_params()
    
    txn = AssetTransferTxn(
        sender=sender,
        sp=params,
        receiver=recipient,
        amt=1,
        index=asset_id
    )
    
    signed_txn = txn.sign(private_key)
    txn_id = client.send_transaction(signed_txn)
    wait_for_confirmation(client, txn_id, wait_rounds=4)
    
    return txn_id


def compute_contract_hash(contract_code: str) -> str:
    """Create a SHA256 fingerprint of the contract code for the NFT metadata."""
    return hashlib.sha256(contract_code.encode()).hexdigest()
