import logging
import uuid
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, get_utc_now

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def is_blocked(block_type: str, value: str) -> bool:
    """Check karta hai ke Telegram ID ya Email blocked_users table mein to nahi."""
    res = supabase.table("blocked_users").select("*").eq("block_type", block_type).eq("block_value", str(value)).execute()
    return len(res.data) > 0

def handle_user_start(user) -> str:
    """Naya user handle karta hai aur status return karta hai."""
    if is_blocked("telegram", str(user.id)):
        return "blocked"
        
    existing = supabase.table("users").select("*").eq("telegram_id", user.id).execute()
    
    if not existing.data:
        try:
            supabase.table("users").insert({
                "telegram_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "is_verified": False,
                "created_at": get_utc_now()
            }).execute()
            return "pending"
        except Exception as e:
            logging.error(f"DB Error: {e}")
            return "error"
            
    is_verified = existing.data[0].get("is_verified", False)
    return "approved" if is_verified else "pending"

def create_auth_session(tg_id: int) -> str:
    """CSRF se bachne ke liye UUID generate karta hai."""
    state_uuid = str(uuid.uuid4())
    supabase.table("auth_sessions").insert({
        "state_uuid": state_uuid,
        "telegram_id": tg_id
    }).execute()
    return state_uuid

def verify_auth_session(state_uuid: str):
    """Callback par UUID check karke delete karta hai."""
    res = supabase.table("auth_sessions").select("telegram_id").eq("state_uuid", state_uuid).execute()
    if res.data:
        supabase.table("auth_sessions").delete().eq("state_uuid", state_uuid).execute()
        return res.data[0]["telegram_id"]
    return None

def save_login_data(tg_id: int, email: str, token_json: dict):
    """Email aur Tokens save karta hai."""
    supabase.table("users").update({
        "email": email,
        "auth_token": token_json,
        "last_login_at": get_utc_now()
    }).eq("telegram_id", tg_id).execute()

def logout_user(tg_id: int) -> bool:
    """User ka token hatata hai aur history save karta hai."""
    user_res = supabase.table("users").select("email").eq("telegram_id", tg_id).execute()
    if user_res.data and user_res.data[0].get("email"):
        email = user_res.data[0]["email"]
        supabase.table("user_history").insert({
            "telegram_id": tg_id,
            "email": email,
            "action": "logged_out",
            "recorded_at": get_utc_now()
        }).execute()
        
        supabase.table("users").update({"auth_token": None}).eq("telegram_id", tg_id).execute()
        return True
    return False

def get_all_users():
    """Admin dashboard ke liye sab users ka data nikalta hai."""
    try:
        res = supabase.table("users").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return []

def update_user_status(tg_id: int, is_verified: bool, status: str, reason: str = ""):
    """Admin actions (Approve/Block) ko handle karta hai naye normalized database ke hisaab se."""
    # 1. Update main users table
    data = {"is_verified": is_verified}
    if status == "approved":
        data["approved_at"] = get_utc_now()
        # Agar pehle se block tha, toh blocked_users list se nikal dein
        supabase.table("blocked_users").delete().eq("block_type", "telegram").eq("block_value", str(tg_id)).execute()
    
    supabase.table("users").update(data).eq("telegram_id", tg_id).execute()

    # 2. Agar block kiya hai, toh blocked_users table mein daal dein
    if status == "blocked":
        # Check karein ke pehle se block to nahi
        res = supabase.table("blocked_users").select("*").eq("block_type", "telegram").eq("block_value", str(tg_id)).execute()
        if not res.data:
            supabase.table("blocked_users").insert({
                "block_type": "telegram",
                "block_value": str(tg_id),
                "reason": reason,
                "blocked_at": get_utc_now()
            }).execute()

def check_admin(email: str) -> bool:
    """Check karta hai ke login karne wala email admin_users table mein hai ya nahi."""
    try:
        res = supabase.table("admin_users").select("*").eq("email", email).execute()
        return len(res.data) > 0
    except Exception as e:
        logging.error(f"Admin Check Error: {e}")
        return False
