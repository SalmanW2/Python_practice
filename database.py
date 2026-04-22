import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, get_utc_now

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def handle_new_user(user):
    """User check karta hai, agar naya ho to save karta hai (first_text time ke sath)"""
    existing = supabase.table("users").select("*").eq("telegram_id", user.id).execute()
    
    if not existing.data:
        try:
            supabase.table("users").insert({
                "telegram_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "status": "pending",
                "first_text": get_utc_now()  # 1st Time
            }).execute()
            return "pending"
        except Exception as e:
            logging.error(f"DB Error: {e}")
            return "error"
            
    return existing.data[0].get("status", "pending")

def update_user_status(tg_id: int, new_status: str):
    """Admin Panel se Status update karta hai"""
    data = {"status": new_status}
    if new_status == "approved":
        data["login_approval"] = get_utc_now()  # 2nd Time (Approval)
    
    supabase.table("users").update(data).eq("telegram_id", tg_id).execute()

def save_login_data(tg_id: str, email: str, token_json: dict):
    """Google Login ke baad Token aur Time save karta hai"""
    supabase.table("users").update({
        "email": email,
        "auth_token": token_json,
        "1st_login": get_utc_now()  # 3rd Time (Login)
    }).eq("telegram_id", int(tg_id)).execute()

def get_all_users():
    """Admin panel ke liye saare users nikalta hai"""
    res = supabase.table("users").select("*").order("first_text", desc=True).execute()
    return res.data
