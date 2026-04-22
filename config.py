import os
from datetime import datetime, timezone

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://python-practice-ennb.onrender.com")

# Missing Variable Validation (Deployment Error Check)
if not all([BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    print("CRITICAL WARNING: Environment variables missing!")

SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.readonly',
    'openid'
]

# UTC Time Generator Function
def get_utc_now():
    return datetime.now(timezone.utc).isoformat()
