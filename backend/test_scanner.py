# test_scanner.py
from scanner import scan_contract

# Test 1: Vulnerable contract — should score LOW (0-40)
vulnerable = """#pragma version 6
txn ApplicationID
bz handle_creation
txn OnCompletion
int NoOp
==
bz reject
byte "balance"
app_global_get
int 1000000
+
byte "balance"
app_global_put
int 1
return
handle_creation:
int 1
return
reject:
int 0
return"""

# Test 2: Safe contract — should score HIGH (71-100)
safe = """#pragma version 6
txn ApplicationID
bz handle_creation
txn OnCompletion
int NoOp
==
bz reject
txn Sender
global CreatorAddress
==
assert
byte "balance"
app_global_get
int 1000000
+
byte "balance"
app_global_put
txn CloseRemainderTo
global ZeroAddress
==
assert
txn RekeyTo
global ZeroAddress
==
assert
int 1
return
handle_creation:
int 1
return
reject:
int 0
return"""

print("Testing VULNERABLE contract...")
result1 = scan_contract(vulnerable)
print(f"Score: {result1['score']} | Risk: {result1['risk_level']}")
print(f"Vulnerabilities: {len(result1['vulnerabilities'])}")
print()

print("Testing SAFE contract...")
result2 = scan_contract(safe)
print(f"Score: {result2['score']} | Risk: {result2['risk_level']}")
print(f"Vulnerabilities: {len(result2['vulnerabilities'])}")
print()

# Assertions
assert result1['score'] < 70, f"FAIL: Vulnerable contract scored too high: {result1['score']}"
assert result2['score'] >= 70, f"FAIL: Safe contract scored too low: {result2['score']}"
assert result1['risk_level'] != result2['risk_level'], "FAIL: Both contracts got same risk level"

print("ALL TESTS PASSED")
