"""Quick test of the risk engine logic"""
from monitoring.risk_engine import evaluate_transaction_risk

tests = {
    "SAFE (0.5 ALGO, no flags)": [
        {"id": "SAFE001", "tx-type": "pay", "fee": 1000, "confirmed-round": 100,
         "payment-transaction": {"amount": 500_000, "receiver": "RECV"}, "note": ""}
    ],
    "WARNING (15k ALGO transfer)": [
        {"id": "WARN001", "tx-type": "pay", "fee": 1000, "confirmed-round": 102,
         "payment-transaction": {"amount": 15_000_000_000, "receiver": "RECV"}, "note": ""}
    ],
    "HIGH (REKEY + drain + 50k ALGO)": [
        {"id": "HIGH001", "tx-type": "pay", "fee": 1000, "confirmed-round": 103,
         "rekey-to": "HACKER_ADDR",
         "payment-transaction": {"amount": 50_000_000_000, "receiver": "RECV", "close-remainder-to": "DRAIN"},
         "note": ""}
    ],
    "HIGH (REKEY only)": [
        {"id": "HIGH002", "tx-type": "pay", "fee": 1000, "confirmed-round": 104,
         "rekey-to": "HACKER_ADDR",
         "payment-transaction": {"amount": 1_000_000, "receiver": "RECV"}, "note": ""}
    ],
}

print("\n" + "="*60)
print("  Risk Engine Calibration Test")
print("="*60)

for label, txns in tests.items():
    results = evaluate_transaction_risk("test-job-calibration", txns)
    for r in results:
        sev = r["severity"]
        icon = {"HIGH": "FAIL", "WARNING": "WARN", "SAFE": "OK  "}.get(sev, "?   ")
        print(f"\n[{icon}] {label}")
        print(f"      severity={sev}  score={r['score']:.3f}  should_alert={r['should_alert']}")
        print(f"      desc: {r['description'][:90]}")

print()
print("Expected:")
print("  SAFE (0.5 ALGO) -> severity=SAFE, should_alert=False")
print("  WARNING (15k ALGO) -> severity=WARNING, should_alert=False")
print("  HIGH (REKEY+drain) -> severity=HIGH, should_alert=True")
print("  HIGH (REKEY only) -> severity=HIGH (REKEY alone = 0.55 * 0.60 = 0.33, actually WARNING)")
print()
