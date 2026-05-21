import joblib
import os
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "algoshield_model.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "label_encoder.pkl")

LABEL_MAP = {"SAFE": "SAFE", "VULNERABLE": "SUSPICIOUS", "RISKY": "RISKY"}

model = None
encoder = None


def load_models():
    """Loads the model and encoder into memory if not already loaded."""
    global model, encoder
    if model is None:
        try:
            model = joblib.load(MODEL_PATH)
        except Exception as e:
            raise RuntimeError(f"Could not load model file at {MODEL_PATH}: {e}")
    if encoder is None:
        try:
            encoder = joblib.load(ENCODER_PATH)
        except Exception as e:
            raise RuntimeError(f"Could not load encoder file at {ENCODER_PATH}: {e}")


def predict(features_dict: dict) -> tuple:
    """Predicts risk class based on input features dictionary."""
    load_models()

    # Expected order for the random forest model according to requirements
    feature_names = [
        "has_rekey_check",
        "has_close_check",
        "has_receiver_check",
        "num_txn",
        "num_and",
        "num_or",
        "contract_length",
        "txn_per_length",
        "logic_density",
        "security_checks",
        "txn_logic_ratio",
    ]

    try:
        feature_vector = np.array([[features_dict[name] for name in feature_names]])
    except KeyError as e:
        raise ValueError(f"Missing expected feature: {e}")

    prediction_num = model.predict(feature_vector)[0]

    raw_label = encoder.inverse_transform([prediction_num])[0]
    prediction_label = LABEL_MAP.get(raw_label, raw_label)

    if hasattr(prediction_num, "item"):
        prediction_num = prediction_num.item()

    return prediction_num, prediction_label
