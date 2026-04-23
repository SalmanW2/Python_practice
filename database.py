import logging
import uuid
import hashlib
import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, get_utc_now

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- NATIVE PASSWORD HASHING (No external libraries needed) ---
def hash_password(password: str) -> str:
    """Hashes a password securely using SHA-256 and a random salt."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pwd_hash.hex()

def verify_hash(password: str, stored_hash: str) -> bool:
    """Verifies a password against a stored salted hash."""
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwd_hash.hex() == hash_hex
    except Exception as e:
        logging.error(f"Hash verification failed: {e}")
        return False

# --- USER ACCESS LOGIC ---

def is_blocked(block_type: str, value: str) -> bool:
    """Checks if a Telegram ID or Email exists in the blocked_users table."""
    res = supabase.table("blocked_users").select("*").eq("block_type", block_type).eq("block_value", str(value)).execute()
    return len(res.data) > 0

def handle_user_start(user) -> str:
    """Handles new user registration and returns their current status."""
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

# --- AUTH SESSION LOGIC (CSRF PROTECTION) ---

def create_auth_session(tg_id: int) -> str:
    """Generates a UUID for CSRF protection during OAuth."""
    state_uuid = str(uuid.uuid4())
    supabase.table("auth_sessions").insert({
        "state_uuid": state_uuid,
        "telegram_id": tg_id
    }).execute()
    return state_uuid

def verify_auth_session(state_uuid: str):
    """Verifies and deletes the UUID upon OAuth callback."""
    res = supabase.table("auth_sessions").select("telegram_id").eq("state_uuid", state_uuid).execute()
    if res.data:
        supabase.table("auth_sessions").delete().eq("state_uuid", state_uuid).execute()
        return res.data[0]["telegram_id"]
    return None

# --- TOKEN & LOGIN LOGIC ---

def save_login_data(tg_id: int, email: str, token_json: dict):
    """Saves OAuth tokens and linked email to the database."""
    supabase.table("users").update({
        "email": email,
        "auth_token": token_json,
        "last_login_at": get_utc_now()
    }).eq("telegram_id", tg_id).execute()

def logout_user(tg_id: int) -> bool:
    """Removes user token and logs the action in history."""
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

# --- ADMIN DASHBOARD DATA FETCHING ---

def get_all_users():
    """Fetches all users for the Admin dashboard."""
    try:
        res = supabase.table("users").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return []

def get_all_blocked():
    """Fetches all blocked records for the blocklist tab."""
    res = supabase.table("blocked_users").select("*").order("blocked_at", desc=True).execute()
    return res.data

def get_all_admins():
    """Fetches all administrators."""
    res = supabase.table("admin_users").select("*").order("created_at", desc=True).execute()
    return res.data

# --- ADMIN ACTIONS & MANAGEMENT ---

def update_user_status(tg_id: int, is_verified: bool, status: str, reason: str = ""):
    """Handles admin actions (Approve/Block/Unblock) and updates database state."""
    data = {"is_verified": is_verified}
    
    if status == "approved":
        data["approved_at"] = get_utc_now()
        supabase.table("blocked_users").delete().eq("block_type", "telegram").eq("block_value", str(tg_id)).execute()
    
    if status == "pending":
        data["approved_at"] = None
        supabase.table("blocked_users").delete().eq("block_type", "telegram").eq("block_value", str(tg_id)).execute()

    supabase.table("users").update(data).eq("telegram_id", tg_id).execute()

    if status == "blocked":
        res = supabase.table("blocked_users").select("*").eq("block_type", "telegram").eq("block_value", str(tg_id)).execute()
        if not res.data:
            supabase.table("blocked_users").insert({
                "block_type": "telegram",
                "block_value": str(tg_id),
                "reason": reason,
                "blocked_at": get_utc_now()
            }).execute()

def remove_blocked_record(record_id: str):
    """Removes a specific block record by its UUID."""
    supabase.table("blocked_users").delete().eq("id", record_id).execute()

def check_admin(email: str) -> bool:
    """Verifies if the email belongs to an administrator."""
    try:
        res = supabase.table("admin_users").select("*").eq("email", email).execute()
        return len(res.data) > 0
    except Exception as e:
        logging.error(f"Admin Check Error: {e}")
        return False

def get_admin_role(email: str) -> str:
    """Returns the specific role of the admin (super_admin or admin)."""
    res = supabase.table("admin_users").select("role").eq("email", email).execute()
    if res.data:
        return res.data[0].get("role", "admin")
    return "admin"

def add_new_admin(email: str, role: str, added_by: str):
    """Inserts a new administrator into the database."""
    supabase.table("admin_users").insert({
        "email": email,
        "role": role,
        "added_by": added_by,
        "created_at": get_utc_now()
    }).execute()

def remove_admin(admin_id: str):
    """Removes an administrator from the database."""
    supabase.table("admin_users").delete().eq("id", admin_id).execute()

# --- ADMIN PASSWORD SECURITY ---

def set_admin_password(email: str, password: str):
    """Hashes and saves a custom password using native Python hashlib."""
    hashed_password = hash_password(password)
    supabase.table("admin_users").update({"password_hash": hashed_password}).eq("email", email).execute()

def verify_admin_password(email: str, password: str) -> bool:
    """Validates the email and password for manual login using native Python hashlib."""
    try:
        res = supabase.table("admin_users").select("password_hash").eq("email", email).execute()
        if not res.data:
            return False
            
        stored_hash = res.data[0].get("password_hash")
        if not stored_hash: 
            return False
            
        return verify_hash(password, stored_hash)
    except Exception as e:
        logging.error(f"Password Verify Error: {e}")
        return False