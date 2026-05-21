# backend/utils/rules_engine.py
import re

RULES = [
    {
        "type": "AUTHORIZATION_MISSING",
        "severity": "Critical",
        "deduction": 30,
        "issue": "No authorization check — any account can call this operation",
        "suggestion": "Add: txn Sender / global CreatorAddress / == / assert",
        "detect": lambda line, ln, code: (
            "app_global_put" in line and
            "txn Sender" not in "\n".join(code.split("\n")[:ln])
        )
    },
    {
        "type": "UNCHECKED_REKEY",
        "severity": "Critical",
        "deduction": 30,
        "issue": "RekeyTo field not verified — attacker can take over account",
        "suggestion": "Add: txn RekeyTo / global ZeroAddress / == / assert",
        "detect": lambda line, ln, code: (
            "RekeyTo" in line and "ZeroAddress" not in line and
            "ZeroAddress" not in "\n".join(code.split("\n")[max(0,ln-3):ln+3])
        )
    },
    {
        "type": "UNCHECKED_CLOSE_REMAINDER",
        "severity": "Critical",
        "deduction": 30,
        "issue": "CloseRemainderTo not rejected — can drain the entire account",
        "suggestion": "Add: txn CloseRemainderTo / global ZeroAddress / == / assert",
        "detect": lambda line, ln, code: (
            "CloseRemainderTo" in line and
            "ZeroAddress" not in "\n".join(code.split("\n")[max(0,ln-3):ln+3])
        )
    },
    {
        "type": "REENTRANCY_RISK",
        "severity": "High",
        "deduction": 15,
        "issue": "Inner transaction before state commit — reentrancy risk",
        "suggestion": "Move all app_global_put operations before itxn_submit",
        "detect": lambda line, ln, code: "itxn_begin" in line
    },
    {
        "type": "MISSING_GROUP_SIZE_CHECK",
        "severity": "High",
        "deduction": 15,
        "issue": "Group transaction count not verified — extra transactions can be injected",
        "suggestion": "Add: global GroupSize / int 1 / == / assert",
        "detect": lambda line, ln, code: (
            "gtxn" in line and "GroupSize" not in code and ln < 5
        )
    },
    {
        "type": "TIMESTAMP_MANIPULATION",
        "severity": "Medium",
        "deduction": 8,
        "issue": "Logic depends on LatestTimestamp which can be manipulated",
        "suggestion": "Add a tolerance margin of ±15 seconds to timestamp comparisons",
        "detect": lambda line, ln, code: "LatestTimestamp" in line
    },
    {
        "type": "INTEGER_OVERFLOW",
        "severity": "Medium",
        "deduction": 8,
        "issue": "Arithmetic without overflow protection",
        "suggestion": "Use addw/mulw instead of +/* and check the carry bit",
        "detect": lambda line, ln, code: (
            line.strip() in ["+", "*"] and
            "addw" not in code and "mulw" not in code
        )
    },
    {
        "type": "HARDCODED_ADDRESS",
        "severity": "Low",
        "deduction": 3,
        "issue": "Hardcoded address — should use global state variable",
        "suggestion": "Store admin address in global state during app creation",
        "detect": lambda line, ln, code: bool(re.search(r"addr [A-Z2-7]{58}", line))
    },
]

def analyze_lines(teal_code: str) -> list:
    lines = teal_code.split("\n")
    found = []
    seen_types = set()

    for ln, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        for rule in RULES:
            if rule["type"] in seen_types:
                continue
            try:
                if rule["detect"](stripped, ln, teal_code):
                    found.append({
                        "line": ln,
                        "vulnerability_type": rule["type"],
                        "issue": rule["issue"],
                        "severity": rule["severity"],
                        "suggestion": rule["suggestion"],
                        "_deduction": rule["deduction"]
                    })
                    seen_types.add(rule["type"])
            except Exception:
                continue

    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    found.sort(key=lambda v: order.get(v["severity"], 4))
    return found

def calculate_score(vulnerabilities: list) -> tuple:
    score = 100
    for v in vulnerabilities:
        score -= v.get("_deduction", 0)
    score = max(0, min(100, score))
    if score <= 40:
        risk = "Critical"
    elif score <= 70:
        risk = "Risky"
    else:
        risk = "Safe"
    return score, risk
