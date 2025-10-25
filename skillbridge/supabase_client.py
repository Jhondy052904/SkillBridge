# skillbridge/supabase_client.py
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase configuration. Check your .env file.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Supabase client initialized successfully from supabase_client.py")
