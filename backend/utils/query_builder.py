"""
query_builder.py
----------------
Converts the extracted + engineered feature dictionary into a rich,
natural language query string for the RAG retrieval pipeline.

The query is deliberately feature-aware and specific — it enumerates
which security checks are missing and which risk signals are active —
so that the ChromaDB semantic search returns the most relevant
vulnerability patterns and fix recommendations.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Severity thresholds (tuned to match the RF model's feature expectations)
# ---------------------------------------------------------------------------
_HIGH_TXN_DENSITY = 0.2       # txn_per_length above this = high transaction density
_HIGH_LOGIC_RATIO = 5.0       # txn_logic_ratio above this = few logic ops per txn access
_LOW_LOGIC_DENSITY = 0.05     # logic_density below this = minimal conditional logic
_LONG_CONTRACT = 80           # contract_length above this = substantial contract


def build_query(features: dict) -> str:
    """
    Convert a feature dictionary into a descriptive natural-language query.

    The query surfaces:
      - Missing security checks (rekey, close, receiver)
      - Risk signals based on computed ratios
      - Relevant structural properties (length, density)

    This makes the semantic search find precise vulnerability patterns
    rather than generic results.

    Args:
        features: Engineered feature dict (output of feature_engineer.engineer_features)

    Returns:
        A rich natural-language query string ready for RAG retrieval.
    """
    parts: list[str] = []
    tags: list[str] = []  # Short keyword tags appended at the end for keyword matching

    # ── Missing Security Checks ──────────────────────────────────────────────
    missing_checks: list[str] = []

    if features.get("has_rekey_check", 0) == 0:
        missing_checks.append("RekeyTo validation")
        tags.extend(["RekeyTo", "account hijack", "rekey vulnerability"])

    if features.get("has_close_check", 0) == 0:
        missing_checks.append("CloseRemainderTo validation")
        tags.extend(["CloseRemainderTo", "balance drain", "close remainder exploit"])

    if features.get("has_receiver_check", 0) == 0:
        missing_checks.append("Receiver address validation")
        tags.extend(["Receiver", "fund redirection", "unauthorized receiver"])

    if missing_checks:
        parts.append(
            "Smart contract is missing critical security checks: "
            + ", ".join(missing_checks)
        )
    else:
        parts.append("Smart contract includes RekeyTo, CloseRemainderTo, and Receiver address validation")

    # ── Security Checks Count Summary ────────────────────────────────────────
    security_checks = features.get("security_checks", 0)
    if security_checks == 0:
        parts.append(
            "No security guard assertions detected — contract may approve all incoming transactions without restriction"
        )
        tags.extend(["logic bomb", "unrestricted approval", "missing assertions"])
    elif security_checks == 1:
        parts.append("Only one security check present — contract has very minimal protection")
    elif security_checks >= 3:
        parts.append("Multiple security checks present — contract has substantial validation coverage")

    # ── Transaction Density Analysis ────────────────────────────────────────
    txn_per_length = features.get("txn_per_length", 0.0)
    txn_logic_ratio = features.get("txn_logic_ratio", 0.0)
    contract_length = features.get("contract_length", 0)

    if txn_per_length > _HIGH_TXN_DENSITY:
        parts.append(
            f"High transaction field access density ({txn_per_length:.3f} txn accesses per line) "
            "suggests many transaction fields are read but potentially not validated"
        )
        tags.append("high transaction density")

    if txn_logic_ratio > _HIGH_LOGIC_RATIO:
        parts.append(
            f"High transaction-to-logic ratio ({txn_logic_ratio:.2f}) indicates many transaction "
            "accesses with few conditional checks — values may be read but not asserted"
        )
        tags.append("unchecked transaction fields")

    # ── Logic Density Analysis ───────────────────────────────────────────────
    logic_density = features.get("logic_density", 0.0)
    num_and = features.get("num_and", 0)
    num_or = features.get("num_or", 0)

    if logic_density < _LOW_LOGIC_DENSITY and contract_length > 20:
        parts.append(
            f"Very low logic density ({logic_density:.4f}) — contract has minimal conditional "
            "branching, meaning most execution paths lead directly to approval without checks"
        )
        tags.extend(["low logic density", "minimal branching", "insufficient validation"])
    elif num_and > 5 or num_or > 3:
        parts.append(
            f"Contract contains {num_and} AND operators and {num_or} OR operators, "
            "indicating relatively complex conditional logic"
        )

    # ── Contract Length Context ──────────────────────────────────────────────
    if contract_length > _LONG_CONTRACT:
        parts.append(
            f"Contract is relatively long ({contract_length} lines), "
            "increasing the surface area for logic bugs and missed validation paths"
        )
    elif contract_length < 15:
        parts.append(
            f"Contract is very short ({contract_length} lines) — "
            "simple contracts are often missing comprehensive security coverage"
        )

    # ── Transaction Count Context ────────────────────────────────────────────
    num_txn = features.get("num_txn", 0)
    if num_txn > 8:
        parts.append(
            f"Contract accesses {num_txn} transaction fields, suggesting it processes "
            "complex multi-field or multi-transaction logic — group transaction attacks may apply"
        )
        tags.append("group transaction complexity")
    elif num_txn == 0:
        parts.append("No transaction field accesses detected — may be a trivial or malformed contract")

    # ── Build Final Query ────────────────────────────────────────────────────
    query_body = ". ".join(parts)

    if tags:
        unique_tags = list(dict.fromkeys(tags))  # Remove duplicates, preserve order
        query_suffix = " | Keywords: " + ", ".join(unique_tags)
    else:
        query_suffix = ""

    return query_body + query_suffix


def get_query_summary(features: dict) -> dict:
    """
    Returns a structured summary of the query's key signals.
    Useful for debugging and for the /suggest response metadata.
    """
    return {
        "missing_checks": [
            check for check, flag in [
                ("RekeyTo", "has_rekey_check"),
                ("CloseRemainderTo", "has_close_check"),
                ("Receiver", "has_receiver_check"),
            ]
            if features.get(flag, 0) == 0
        ],
        "security_check_count": features.get("security_checks", 0),
        "logic_density": round(features.get("logic_density", 0.0), 4),
        "txn_logic_ratio": round(features.get("txn_logic_ratio", 0.0), 2),
        "contract_length": features.get("contract_length", 0),
    }
