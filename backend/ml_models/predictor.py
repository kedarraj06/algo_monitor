"""
predictor.py
------------
Clean wrapper around the existing inference logic.
Provides an object-oriented Predictor class to keep the app.py clean.
"""

from ml_models.inference import predict as legacy_predict

LABEL_MAP = {"SAFE": "SAFE", "VULNERABLE": "SUSPICIOUS", "RISKY": "RISKY"}


class Predictor:
    @staticmethod
    def predict(features_dict: dict) -> tuple:
        """
        Runs the exact same Random Forest model loaded by inference.py.
        Returns: (prediction_number, prediction_label)
        """
        prediction_num, prediction_label = legacy_predict(features_dict)
        standardized_label = LABEL_MAP.get(prediction_label, prediction_label)
        return prediction_num, standardized_label
