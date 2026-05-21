"""
suggester.py
------------
Orchestration layer for Algorand TEAL security suggestions.

Combines deterministic rule-based analysis (based on feature vectors)
with dynamic Retrieval-Augmented Generation (RAG) using a local SLM.
Includes LRU caching, Security Score UI derivation, and TEAL line mapping.
"""

from typing import List, Dict, Any
import re
import json
import logging
import hashlib
from functools import lru_cache

from utils.query_builder import build_query
from utils.rag_pipeline import retrieve_context, run_slm

logger = logging.getLogger(__name__)

# Severity Weights for Security Score mapping
SEVERITY_WEIGHTS = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 10, "LOW": 5, "Critical": 25, "High": 15, "Medium": 10, "Low": 5}


def map_issue_to_lines(issue_id: str, content: str) -> List[int]:
    """
    Scans the raw TEAL content using heuristics to find line numbers
    relevant to the documented vulnerability.
    """
    lines = content.split("\n")
    found_lines = []

    if "RekeyTo" in issue_id:
        for i, line in enumerate(lines):
            if "RekeyTo" in line or "rekey" in line.lower():
                found_lines.append(i + 1)

    elif "CloseRemainderTo" in issue_id:
        for i, line in enumerate(lines):
            if "CloseRemainderTo" in line or "close" in line.lower():
                found_lines.append(i + 1)

    elif "Receiver" in issue_id:
        for i, line in enumerate(lines):
            if "Receiver" in line:
                found_lines.append(i + 1)

    elif "Logic Bomb" in issue_id:
        # For missing assertions, we highlight where returns or success conditions are
        for i, line in enumerate(lines):
            if "return" in line or "int 1" in line:
                found_lines.append(i + 1)

    return found_lines[:3]  # Return max 3 line numbers for UI


def get_rule_based_suggestions(
    features: Dict[str, Any], content: str
) -> List[Dict[str, Any]]:
    """
    Generate deterministic suggestions based purely on the extracted features.
    """
    suggestions = []

    # 1. RekeyTo Check
    if features.get("has_rekey_check", 0) == 0:
        lines = map_issue_to_lines("RekeyTo", content)
        suggestions.append(
            {
                "id": "RekeyTo",
                "issue": "Missing RekeyTo Validation",
                "severity": "Critical",
                "source": "rule-based",
                "explanation": "The contract does not appear to check that the RekeyTo field is set to the ZeroAddress. This leaves the contract vulnerable to an account hijack, where an attacker rekeys the escrow account to themselves.",
                "fix": "Add the following assertion before approving any transaction:\ntxn RekeyTo\nglobal ZeroAddress\n==\nassert",
                "suggestion": "Add an assertion that Txn.rekey_to() equals the zero address.",
                "lines": lines,
                "line": lines[0] if lines else 1,
            }
        )

    # 2. CloseRemainderTo Check
    if features.get("has_close_check", 0) == 0:
        lines = map_issue_to_lines("CloseRemainderTo", content)
        suggestions.append(
            {
                "id": "CloseRemainderTo",
                "issue": "Missing CloseRemainderTo Validation",
                "severity": "Critical",
                "source": "rule-based",
                "explanation": "The contract does not validate the CloseRemainderTo field. An attacker could set this to their own address, draining the entire contract balance in a single transaction regardless of amount limits.",
                "fix": "Add the following assertion to prevent balance sweeping:\ntxn CloseRemainderTo\nglobal ZeroAddress\n==\nassert",
                "suggestion": "Add an assertion that Txn.close_remainder_to() equals the zero address.",
                "lines": lines,
                "line": lines[0] if lines else 1,
            }
        )

    # 3. Receiver Check
    if features.get("has_receiver_check", 0) == 0 and features.get("num_txn", 0) > 0:
        lines = map_issue_to_lines("Receiver", content)
        suggestions.append(
            {
                "id": "Receiver",
                "issue": "Unvalidated Receiver Address",
                "severity": "High",
                "source": "rule-based",
                "explanation": "The contract accesses transaction fields but does not explicitly validate the Receiver address. This can allow attackers to redirect approved funds to their own addresses.",
                "fix": "Compare the receiver against a known safe address:\ntxn Receiver\naddr EXPECTED_ADDRESS\n==\nassert",
                "suggestion": "Ensure the receiver address is validated against a whitelist or expected address.",
                "lines": lines,
                "line": lines[0] if lines else 1,
            }
        )

    # 4. Logic Density Exception (Logic Bomb / Unrestricted Approval)
    if features.get("security_checks", 0) <= 1 and features.get("num_txn", 0) > 0:
        lines = map_issue_to_lines("Logic Bomb", content)
        suggestions.append(
            {
                "id": "Logic Bomb",
                "issue": "Insufficient Security Guards (Logic Bomb pattern)",
                "severity": "High",
                "source": "rule-based",
                "explanation": "The contract touches transaction fields but has 1 or fewer security assertions. This likely indicates an open-ended approval path where most transactions succeed regardless of intent.",
                "fix": "Ensure critical paths check TypeEnum, Fee, RekeyTo, CloseRemainderTo, and perform amount boundary checks.",
                "suggestion": "Add more explicit security assertions to critical logic paths.",
                "lines": lines,
                "line": lines[0] if lines else 1,
            }
        )

    return suggestions


def merge_rag_suggestions(
    rule_based: List[Dict], rag_output: Dict, context_chunks: List
) -> List[Dict]:
    """
    Intelligently merges the structured JSON SLM response with existing rules.
    If the text overlaps with missing RekeyTo or CloseRemainderTo, enrich it.
    Else, append the new RAG insight.
    """
    issue_lower = rag_output.get("issue", "").lower()
    exp_lower = rag_output.get("explanation", "").lower()

    merged = False
    for rule in rule_based:
        rule_issue = rule["issue"].lower()
        if "rekey" in issue_lower and "rekey" in rule_issue:
            rule["explanation"] += (
                f"\n\n[AI Context Enriched]: {rag_output['explanation']}"
            )
            if rag_output.get("fix") and len(rag_output["fix"]) > 10:
                rule["fix"] = f"{rule['fix']}\n\nAI Suggested Fix:\n{rag_output['fix']}"
            merged = True
            break
        elif "close" in issue_lower and "close" in rule_issue:
            rule["explanation"] += (
                f"\n\n[AI Context Enriched]: {rag_output['explanation']}"
            )
            merged = True
            break

    if not merged:
        source_context = (
            context_chunks[0]["source"] if context_chunks else "knowledge_base"
        )
        rule_based.append(
            {
                "id": "RAG_Insight",
                "issue": rag_output.get("issue", "AI Generated Security Insight"),
                "severity": "Medium",  # Safe default
                "source": f"RAG ({source_context})",
                "explanation": rag_output.get(
                    "explanation", "Review context for details."
                ),
                "fix": rag_output.get("fix", ""),
                "suggestion": rag_output.get("fix", "Review context for details."),
                "line": rag_output.get("line", 1) or 1,
                "lines": [],
            }
        )

    return rule_based


def get_rag_suggestions(features: Dict[str, Any], rule_based: List[Dict]) -> List[Dict]:
    """
    Uses the query builder to search the knowledge base,
    then queries the local SLM to summarize it into an actionable fix.
    """
    query = build_query(features)

    # 1. Retrieve knowledge base context
    context_chunks = retrieve_context(query, top_k=3)
    if not context_chunks:
        return rule_based

    # 2. Extract structured SLM response
    slm_response = run_slm(query, context_chunks)

    if not slm_response:
        # Fallback: Just formulate a suggestion from the top retrieved snippet
        top_snippet = context_chunks[0]
        rule_based.append(
            {
                "id": "KB_Fallback",
                "issue": f"Relevant Security Standard: {top_snippet['source']}",
                "severity": "LOW",
                "source": "knowledge_base",
                "explanation": f"Based on structural similarity, the following rule is highly relevant to your contract:\n\n{top_snippet['text'][:300]}...",
                "fix": "",
                "lines": [],
            }
        )
        return rule_based

    # Successfully ran SLM, merge intelligently
    return merge_rag_suggestions(rule_based, slm_response, context_chunks)


def calculate_security_score(prediction_label: str, suggestions: List[Dict]) -> int:
    """
    Calculates a 0-100 score based on severity weights and prediction class.

    Logic:
    - SAFE: baseline 100, max 100
    - SUSPICIOUS: baseline 85, max 85
    - RISKY: baseline 50, max 50

    Deductions:
    - CRITICAL: -25
    - HIGH: -15
    - MEDIUM: -10
    - LOW: -5

    Final score is clamped between 0-100.
    """
    baseline_map = {"SAFE": 100, "SUSPICIOUS": 85, "RISKY": 50}
    max_score_map = {"SAFE": 100, "SUSPICIOUS": 85, "RISKY": 50}

    baseline = baseline_map.get(prediction_label, 50)
    max_score = max_score_map.get(prediction_label, 50)

    deduction = sum(SEVERITY_WEIGHTS.get(s["severity"].upper(), 0) for s in suggestions)
    score = baseline - deduction

    return max(0, min(max_score, score))


@lru_cache(maxsize=32)
def cached_generate_suggestions(
    content_hash: str, features_json: str, prediction_label: str
) -> tuple:
    """
    Cached worker for generation. LRU cache prevents repeated SLM loads for the exact same file.
    """
    features = json.loads(features_json)
    content_raw = content_hash.split("::CONTENT::")[
        1
    ]  # Hack to pass content without breaking LRU

    # Always run rule-based suggestions
    results = get_rule_based_suggestions(features, content_raw)

    # Attempt RAG-based suggestion modification
    try:
        results = get_rag_suggestions(features, results)
    except Exception as e:
        logger.error(f"RAG suggestion failed: {e}")
        pass

    score = calculate_security_score(prediction_label, results)
    return results, score


def generate_suggestions(
    features: Dict[str, Any], content: str, prediction_label: str
) -> tuple:
    """
    Main entry point for generating security suggestions.
    Handles caching JSON serialization.
    Returns: (suggestions_list, security_score)
    """
    # Create deterministic hash string for caching
    content_hash = hashlib.md5(content.encode()).hexdigest() + "::CONTENT::" + content
    features_json = json.dumps(features, sort_keys=True)

    return cached_generate_suggestions(content_hash, features_json, prediction_label)

def get_suggestions(contract_code: str) -> dict:
    """
    Exposed API for the /suggest endpoint.
    Returns structured JSON compatible with the frontend SuggestionPanel.
    """
    from utils.feature_extractor import extract_features_from_teal
    from utils.feature_engineer import engineer_features
    from ml_models.inference import predict

    # Extract features and run prediction
    extracted = extract_features_from_teal(contract_code)
    features = engineer_features(extracted)
    prediction_num, prediction_label = predict(features)

    # Get suggestions and score
    suggestions_list, score = generate_suggestions(features, contract_code, prediction_label)

    # Format the summary based on score
    summary = f"Security Analysis: {prediction_label}"
    if score >= 70:
        summary = "Contract appears generally safe, but review minor suggestions."
    elif score >= 40:
        summary = "Contract is suspicious. Address the highlighted vulnerabilities."
    else:
        summary = "Contract is highly risky. Do not deploy without fixing critical issues."

    # Format the suggestions into the expected schema
    formatted_suggestions = []
    for s in suggestions_list:
        line = s.get("line", 0)
        if not line and s.get("lines"):
            line = s["lines"][0]
        formatted_suggestions.append({
            "line": line,
            "vulnerability": s.get("issue", "Unknown vulnerability"),
            "description": s.get("explanation", "No description provided"),
            "fix": s.get("fix", "Review context for details"),
            "severity": s.get("severity", "Medium").capitalize()
        })

    return {
        "security_score": score,
        "suggestions": formatted_suggestions,
        "summary": summary
    }
