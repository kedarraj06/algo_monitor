import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Fallback values for environment variables. Ensure these are set in .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Remove /rest/v1/ if the user appended it accidentally
if SUPABASE_URL and SUPABASE_URL.endswith("/rest/v1/"):
    SUPABASE_URL = SUPABASE_URL.replace("/rest/v1/", "")
elif SUPABASE_URL and SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL.replace("/rest/v1", "")

_supabase_client: Client = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
        
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
        
    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise
