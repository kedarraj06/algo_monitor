# monitor.py
# This file will be replaced by the AI developer's implementation.
# It must export: get_monitor(app_id: str) -> ContractMonitor

class StubMonitor:
    def add_transactions(self, transactions):
        pass
    def check_transaction(self, transaction):
        return {"is_anomaly": False, "anomaly_score": 0.0, "description": "Stub monitor", "severity": "info"}

def get_monitor(app_id: str):
    return StubMonitor()
