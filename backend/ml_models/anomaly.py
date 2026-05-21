# backend/ml_models/anomaly.py
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime

class ContractMonitor:
    def __init__(self, app_id):
        self.app_id = app_id
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.history = []
        self.is_trained = False

    def _features(self, txn):
        pay = txn.get("payment-transaction", {})
        return [
            float(pay.get("amount", 0)),
            float(txn.get("fee", 1000)),
            float(len(txn.get("note", "") or "")),
            1.0 if txn.get("rekey-to") else 0.0,
            1.0 if pay.get("close-remainder-to") else 0.0,
            float(len(txn.get("inner-txns", []) or [])),
        ]

    def add_transactions(self, txns):
        for t in txns:
            self.history.append(self._features(t))
        if len(self.history) >= 10:
            self.model.fit(np.array(self.history))
            self.is_trained = True

    def check_transaction(self, txn):
        if not self.is_trained:
            return {"is_anomaly": False, "anomaly_score": 0.0, "description": "Collecting baseline", "severity": "info"}
        f = np.array([self._features(txn)])
        pred = self.model.predict(f)[0]
        score = round(max(0.0, min(1.0, (-self.model.score_samples(f)[0] - 0.3) * 2)), 3)
        is_anom = pred == -1
        sev = ("Critical" if score > 0.8 else "High" if score > 0.6 else "Medium" if score > 0.4 else "Low") if is_anom else "normal"
        flags = []
        pay = txn.get("payment-transaction", {})
        if pay.get("amount", 0) > 1_000_000_000: flags.append(f"Large transfer: {pay['amount']/1e6:.1f} ALGO")
        if txn.get("rekey-to"): flags.append("REKEY operation detected")
        if pay.get("close-remainder-to"): flags.append("CLOSE_REMAINDER_TO detected")
        desc = " | ".join(flags) if flags else f"Statistical anomaly (score: {score:.2f})"
        return {"is_anomaly": is_anom, "anomaly_score": score, "description": desc, "severity": sev, "timestamp": datetime.utcnow().isoformat()}

_monitors = {}
def get_monitor(app_id):
    if app_id not in _monitors:
        _monitors[app_id] = ContractMonitor(app_id)
    return _monitors[app_id]
