# backend/test_monitor_api_e2e.py
import httpx
import json
import sys

def run_test():
    print("=" * 60)
    print("  AlgoShield AI — Protocol E2E API Verification")
    print("=" * 60)

    # 1. Start live monitoring with real Folks Finance App ID & FeeSink Address
    url = "http://127.0.0.1:8000/monitor/start"
    payload = {
        "wallet_address": "GD64F7W4H2L67UIEVEQHCAQQFYASVPVELUC5SGBJ6RA6AKXIXFFBVPQLVT",
        "app_id": 971350278,
        "account_address": "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA",
        "alert_email": "programmingla04@gmail.com",
        "telegram_chat_id": "987654321"
    }

    print("1. Sending /monitor/start POST request with real Mainnet data...")
    try:
        response = httpx.post(url, json=payload, timeout=25.0)
        print(f"   Status Code: {response.status_code}")
        data = response.json()
        print(f"   Response Body: {json.dumps(data, indent=2)}")
        
        job_id = data.get("job_id")
        initial_status = data.get("initial_status")
        explanation = data.get("explanation")
        
        assert response.status_code == 200, "API call failed!"
        assert job_id is not None, "Job ID not returned!"
        assert initial_status is not None, "Initial status not returned!"
        assert explanation is not None, "Explanation not returned!"
        print("   [SUCCESS] Baseline scan returned successfully!")
    except Exception as e:
        print(f"   [ERROR] /monitor/start error: {str(e).encode('ascii', 'ignore').decode('ascii')}")
        sys.exit(1)

    # 2. Fetch history of alerts to verify persistence
    alerts_url = f"http://127.0.0.1:8000/monitor/971350278/alerts"
    params = {"wallet_address": "GD64F7W4H2L67UIEVEQHCAQQFYASVPVELUC5SGBJ6RA6AKXIXFFBVPQLVT"}
    
    print("\n2. Querying historical alerts endpoint to verify persistence...")
    try:
        alerts_res = httpx.get(alerts_url, params=params, timeout=15.0)
        print(f"   Status Code: {alerts_res.status_code}")
        alerts_data = alerts_res.json()
        print(f"   Alerts Count: {len(alerts_data.get('alerts', []))}")
        
        alerts = alerts_data.get("alerts", [])
        assert len(alerts) > 0, "No alerts found in DB!"
        
        # Check that the startup baseline alert matches the scan details
        startup_alert = [a for a in alerts if "Monitoring Started" in a.get("description", "")]
        assert len(startup_alert) > 0, "Initial baseline alert was not persisted in DB!"
        print(f"   [SUCCESS] Baseline alert persisted in DB: {startup_alert[0]['description']}")
    except Exception as e:
        print(f"   [ERROR] History fetch error: {str(e).encode('ascii', 'ignore').decode('ascii')}")
        sys.exit(1)

    # 3. Stop monitoring cleanly
    stop_url = f"http://127.0.0.1:8000/monitor/stop/{job_id}"
    print("\n3. Stopping monitoring job cleanly...")
    try:
        stop_res = httpx.post(stop_url, timeout=15.0)
        print(f"   Status Code: {stop_res.status_code}")
        print(f"   Response Body: {stop_res.json()}")
        assert stop_res.status_code == 200, "Stop API call failed!"
        print("   [SUCCESS] Live monitoring job unregistered successfully!")
    except Exception as e:
        print(f"   [ERROR] Stop monitor error: {str(e).encode('ascii', 'ignore').decode('ascii')}")
        sys.exit(1)

    print("=" * 60)
    print("  [SUCCESS] Protocol E2E API Verification PASSED successfully!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
