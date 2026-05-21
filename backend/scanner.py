# scanner.py
import os
import json
from utils.feature_extractor import extract_features_from_teal
from utils.feature_engineer import engineer_features
from ml_models.inference import predict
from ml_models import suggester
from ml_models import slm_inference
from dotenv import load_dotenv

load_dotenv()

def scan_contract(contract_code: str) -> dict:
    """
    Analyze a TEAL smart contract for security vulnerabilities using the locally trained ML model.

    Args:
        contract_code: Raw string of the smart contract code

    Returns:
        dict with score, risk_level, vulnerabilities, summary
    """
    print("=== SCANNER DEBUG (ML MODEL) ===")
    print(f"Contract length: {len(contract_code)} characters")

    if not contract_code or not contract_code.strip():
        return {
            "score": 0,
            "risk_level": "Critical",
            "vulnerabilities": [],
            "summary": "Empty contract provided."
        }

    try:
        # Extract base features
        extracted = extract_features_from_teal(contract_code)
        
        # Add engineered features
        engineered = engineer_features(extracted.copy())
        
        # Predict using the custom ML model
        prediction_num, prediction_label = predict(engineered)
        
        print(f"ML Prediction: Num={prediction_num}, Label={prediction_label}")

        label_lower = prediction_label.lower()
        
        # Map label to our standard risk levels
        if "safe" in label_lower or "low" in label_lower:
            base_score = 100
        elif "vulnerable" in label_lower or "critical" in label_lower or "high" in label_lower:
            base_score = 40
        else: # suspicious, risky, medium
            base_score = 70

        # Vulnerabilities are now generated entirely by the AI/RAG engine
        vulnerabilities = []

        # Enforce score bounds
        final_score = max(0, min(100, base_score))

        # Re-enforce risk level based on the newly calculated score
        if final_score <= 40:
            risk_level = "Critical"
        elif final_score <= 70:
            risk_level = "Risky"
        else:
            risk_level = "Safe"

        summary = f"Custom ML model evaluated this contract as {prediction_label}. "
        if len(vulnerabilities) > 0:
            summary += f"Identified {len(vulnerabilities)} structural concerns missing standard checks."
        else:
            summary += "Standard security checks appear to be present."

        suggestions_list = []
        try:
            suggestions_list, security_score = suggester.generate_suggestions(
                engineered, contract_code, prediction_label
            )
            # If the suggester computed a different score (e.g., from RAG rules), update it
            if security_score != final_score:
                final_score = security_score
                if final_score <= 40:
                    risk_level = "Critical"
                elif final_score <= 70:
                    risk_level = "Risky"
                else:
                    risk_level = "Safe"
        except Exception as e:
            print(f"[Suggester] Failed: {e}")

        # Combine rule-based vulnerabilities with AI suggestions
        # so the frontend displays the rich AI output immediately
        for s in suggestions_list:
            if "line" not in s:
                s["line"] = s.get("lines", [1])[0] if s.get("lines") else 1
            if "vulnerability_type" not in s:
                s["vulnerability_type"] = s.get("id", "AI_INSIGHT")

        return {
            "score": int(final_score),
            "risk_level": risk_level,
            "vulnerabilities": vulnerabilities + suggestions_list,
            "suggestions": suggestions_list,
            "summary": summary,
            "slm_explanation": None,
            "slm_suggestions": None,
            "label": prediction_label
        }

    except Exception as e:
        print(f"[AlgoShield ML Scanner] Unexpected error: {e}")
        return {
            "score": 50,
            "risk_level": "Risky",
            "vulnerabilities": [],
            "summary": "ML Scan failed due to an unexpected error.",
            "error": str(e)
        }
