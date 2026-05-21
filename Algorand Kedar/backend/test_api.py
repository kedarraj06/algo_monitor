from fastapi.testclient import TestClient
from app import app
import os
import sys

client = TestClient(app)

def test_analyze():
    # Find a sample teal file
    possible_dir = r"e:/Algoshiled_AI/contracts/safe"
    files = [f for f in os.listdir(possible_dir) if f.endswith(".teal")]
    if not files:
        print("No .teal files found to test.")
        sys.exit(1)
        
    sample_teal = os.path.join(possible_dir, files[0])
    
    with open(sample_teal, "rb") as f:
        response = client.post("/analyze", files={"file": ("test.teal", f, "application/octet-stream")})
        
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("Test Passed")
    else:
        print("Test Failed")

if __name__ == "__main__":
    try:
        test_analyze()
    except Exception as e:
        print(f"Error during testing: {e}")
