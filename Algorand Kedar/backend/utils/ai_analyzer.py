"""
ai_analyzer.py
--------------
Thin adapter that bridges transaction data from the monitoring loop
into the existing TEAL feature extraction + ML prediction pipeline.

Design principle:
  - Does NOT modify the existing extraction/prediction logic in any way.
  - Simply serializes transaction dicts into a string format that
    extract_features_from_teal() can meaningfully process.
  - Returns a structured result dict for the monitoring loop to act on.

Risk thresholds:
  - "RISKY"      → high risk, store alert with risk_level="HIGH"
  - "SUSPICIOUS" → medium risk, store alert with risk_level="MEDIUM"
  - "SAFE"       → no alert
"""

import json
import logging
from utils.feature_extractor import extract_features_from_teal
from utils.feature_engineer import engineer_features
from models.inference import predict

logger = logging.getLogger(__name__)

# Labels that trigger an alert
RISKY_LABELS = {"RISKY", "SUSPICIOUS"}

# Maps prediction label to alert risk_level string
RISK_LEVEL_MAP = {
    "RISKY": "HIGH",
    "SUSPICIOUS": "MEDIUM",
    "SAFE": "SAFE",
}


def _serialize_transaction(txn: dict) -> str:
    """
    Convert a raw Algorand indexer transaction dict into a flat text string
    that mimics the token-based structure of a TEAL file, so that
    extract_features_from_teal() can operate on it.

    Strategy:
      - Flatten the full JSON into a readable key-value string
      - Preserve field names and values as tokens on separate lines
      - This allows the feature extractor to count txn references,
        security-relevant fields (Receiver, RekeyTo, CloseRemainderTo),
        and logical operators found in note/args fields.
    """
    lines = []

    def _flatten(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _flatten(v, prefix=f"{prefix}{k} ")
        elif isinstance(obj, list):
            for item in obj:
                _flatten(item, prefix=prefix)
        else:
            lines.append(f"{prefix}{obj}")

    _flatten(txn)
    return "\n".join(lines)


def analyze_transaction(txn: dict) -> dict:
    """
    Analyze a single transaction dict using the existing ML pipeline.

    Returns a result dict:
    {
        "txn_id":       str,
        "label":        str,      # "SAFE", "SUSPICIOUS", or "RISKY"
        "prediction":   int,
        "risk_level":   str,      # "SAFE", "MEDIUM", or "HIGH"
        "is_risky":     bool,
        "error":        str | None
    }
    """
    txn_id = txn.get("id", "UNKNOWN")

    try:
        # Step 1: Serialize transaction dict → string
        txn_str = _serialize_transaction(txn)

        # Step 2: Reuse the existing TEAL feature extraction pipeline
        extracted = extract_features_from_teal(txn_str)

        # Step 3: Engineer derived features
        engineered = engineer_features(extracted)

        # Step 4: Run existing ML prediction model
        prediction_num, prediction_label = predict(engineered)

        risk_level = RISK_LEVEL_MAP.get(prediction_label, "SAFE")
        is_risky = prediction_label in RISKY_LABELS

        logger.debug(
            f"[AI] TXN {txn_id} -> label={prediction_label} | "
            f"risk_level={risk_level} | features={engineered}"
        )

        return {
            "txn_id": txn_id,
            "label": prediction_label,
            "prediction": prediction_num,
            "risk_level": risk_level,
            "is_risky": is_risky,
            "error": None,
        }

    except Exception as e:
        logger.error(f"[AI] Failed to analyze TXN {txn_id}: {e}")
        return {
            "txn_id": txn_id,
            "label": "UNKNOWN",
            "prediction": -1,
            "risk_level": "UNKNOWN",
            "is_risky": False,
            "error": str(e),
        }
