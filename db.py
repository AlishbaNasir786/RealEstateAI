import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = None

try:
    from supabase import create_client, Client
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Warning: Failed to initialize Supabase client: {e}")
    else:
        print("Note: Running in offline local DB mode (SUPABASE_URL not configured).")
except ImportError:
    print("Warning: supabase package not installed. Running without Supabase.")

