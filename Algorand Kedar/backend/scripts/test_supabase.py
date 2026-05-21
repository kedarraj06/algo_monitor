import os
import sys
from dotenv import load_dotenv

# Add parent directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from utils.supabase_client import get_supabase_client

def test_supabase():
    try:
        supabase = get_supabase_client()
        print("Supabase client initialized.")
        
        # Try reading to see if tables exist
        try:
            print("Attempting to read from monitored_contracts...")
            response = supabase.table("monitored_contracts").select("*").limit(1).execute()
            print("Read successful! Tables exist.")
            print(f"Data: {response.data}")
            return True
        except Exception as e:
            print(f"Read failed. Tables likely do not exist. Error: {e}")
            return False
            
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        return False

if __name__ == "__main__":
    test_supabase()
