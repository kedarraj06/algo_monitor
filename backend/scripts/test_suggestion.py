"""
test_suggestion.py
------------------
Tests the /suggest endpoint of the AlgoShieldAI backend.
Sends a sample TEAL contract and pretty-prints the response.

Run from the project root:
    python scripts/test_suggestion.py [path/to/contract.teal]
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Try to import requests; provide helpful error message if missing
try:
    import requests
except ImportError:
    print("[ERROR] 'requests' package not installed. Run: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
SUGGEST_ENDPOINT = f"{BACKEND_URL}/suggest"
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze"

# Sample vulnerable TEAL contract for testing (intentionally missing security checks)
SAMPLE_VULNERABLE_TEAL = """#pragma version 6
// Sample vulnerable TEAL - Missing RekeyTo and CloseRemainderTo checks
txn TypeEnum
int pay
==
assert
txn Amount
int 1000000
>=
assert
txn Receiver
addr AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
==
assert
int 1
"""

SAMPLE_SAFE_TEAL = """#pragma version 6
// Sample safe TEAL with all required security checks
txn RekeyTo
global ZeroAddress
==
assert
txn CloseRemainderTo
global ZeroAddress
==
assert
txn TypeEnum
int pay
==
assert
txn Fee
global MinTxnFee
==
assert
txn Amount
int 1000000
>=
assert
txn Receiver
addr AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
==
assert
int 1
"""


def print_separator(char="─", width=60):
    print(char * width)


def print_header(title: str):
    print_separator("═")
    print(f"  {title}")
    print_separator("═")


def pretty_print_suggestions(data: dict):
    """Pretty print the /suggest response."""
    print(f"\n  Prediction : {data.get('label', 'N/A')}")
    print(f"  Security Score : {data.get('score', 'N/A')}/100")

    suggestions = data.get("suggestions", [])
    if not suggestions:
        print("\n  [INFO] No suggestions returned.")
        return

    print(f"\n  Suggestions ({len(suggestions)} found):")
    print_separator()

    for i, suggestion in enumerate(suggestions, 1):
        severity = suggestion.get("severity", "MEDIUM")
        severity_icons = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "CRITICAL": "🔴⚠️"}
        icon = severity_icons.get(severity, "⚪")

        print(f"\n  [{i}] {icon} {suggestion.get('issue', 'Unknown Issue')} [{severity}]")
        print(f"      Source    : {suggestion.get('source', 'rule-based')}")
        
        lines = suggestion.get("lines", [])
        if lines:
            print(f"      Lines     : {', '.join(map(str, lines))}")
            
        print()
        explanation = suggestion.get("explanation", "No explanation provided.")
        # Word-wrap explanation at 70 chars
        words = explanation.split()
        line = "      "
        for word in words:
            if len(line) + len(word) > 72:
                print(line)
                line = "      " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)

        print()
        fix = suggestion.get("fix", "No fix provided.")
        if fix:
            print("      Fix:")
            for fix_line in fix.split("\n"):
                print(f"        {fix_line}")

        if i < len(suggestions):
            print_separator("·")


def test_endpoint(teal_content: str, label: str = "Test Contract") -> bool:
    """Send a TEAL contract to /suggest and display results."""
    print(f"\n  Testing: {label}")
    print_separator()

    # Write to a temp file
    with tempfile.NamedTemporaryFile(suffix=".teal", delete=False, mode="w", encoding="utf-8") as f:
        f.write(teal_content)
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as f:
            response = requests.post(
                SUGGEST_ENDPOINT,
                files={"file": ("test_contract.teal", f, "application/octet-stream")},
                timeout=60
            )

        if response.status_code == 200:
            data = response.json()
            pretty_print_suggestions(data)
            return True
        else:
            print(f"\n  [ERROR] HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Detail: {error_data.get('detail', response.text)}")
            except Exception:
                print(f"  Response: {response.text[:300]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"\n  [ERROR] Connection refused. Is the backend running?")
        print(f"  Start it with: uvicorn app:app --host 127.0.0.1 --port 8000 --reload")
        print(f"  (from the backend/ directory)")
        return False
    except requests.exceptions.Timeout:
        print(f"\n  [ERROR] Request timed out after 60 seconds.")
        return False
    except Exception as e:
        print(f"\n  [ERROR] Unexpected error: {e}")
        return False
    finally:
        os.unlink(tmp_path)


def check_backend_health():
    """Check if the backend is reachable."""
    try:
        resp = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def main():
    print_header("AlgoShieldAI — Suggestion Endpoint Test")
    print(f"\n  Backend: {BACKEND_URL}")

    # Health check
    print("\n[STEP 1] Checking backend connectivity...")
    if not check_backend_health():
        print(f"  [WARN] Backend at {BACKEND_URL} may not be healthy, but proceeding...")
    else:
        print("  [OK] Backend is reachable")

    # Check for custom contract file
    custom_file = sys.argv[1] if len(sys.argv) > 1 else None

    if custom_file:
        # Test user-provided contract
        print(f"\n[STEP 2] Testing user-provided contract: {custom_file}")
        contract_path = Path(custom_file)
        if not contract_path.exists():
            print(f"  [ERROR] File not found: {custom_file}")
            sys.exit(1)
        content = contract_path.read_text(encoding="utf-8")
        success = test_endpoint(content, label=contract_path.name)
    else:
        # Test with built-in samples
        print("\n[STEP 2] Testing with built-in sample contracts...")

        results = []

        # Test 1: Vulnerable contract
        print_header("Test 1: Vulnerable Contract (Expected: RISKY/SUSPICIOUS)")
        success1 = test_endpoint(SAMPLE_VULNERABLE_TEAL, "Vulnerable TEAL (No Security Checks)")
        results.append(("Vulnerable Contract", success1))

        # Test 2: Safe contract
        print_header("Test 2: Safe Contract (Expected: SAFE)")
        success2 = test_endpoint(SAMPLE_SAFE_TEAL, "Safe TEAL (All Checks Present)")
        results.append(("Safe Contract", success2))
        
        # Test 3: Empty contract
        print_header("Test 3: Empty Contract (Edge Case)")
        success3 = test_endpoint("", "Empty Contract")
        results.append(("Empty Contract", success3))
        
        # Test 4: Small contract
        print_header("Test 4: Small Contract (Edge Case)")
        success4 = test_endpoint("#pragma version 6\nint 1", "Small Contract")
        results.append(("Small Contract", success4))
        
        # Test 5: Large contract
        print_header("Test 5: Large Contract (Edge Case)")
        large_content = "#pragma version 6\n" + (SAMPLE_SAFE_TEAL * 10)
        success5 = test_endpoint(large_content, "Large Contract")
        results.append(("Large Contract", success5))

        # Summary
        print_header("Test Summary")
        all_passed = True
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}  {test_name}")
            if not passed:
                all_passed = False

        print()
        sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
