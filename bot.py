import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from supabase import create_client, Client
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Environment Variables Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://python-practice-ennb.onrender.com")

# Google Scopes (Permissions)
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.readonly',
    'openid'
]

# Initialize Supabase and Telegram Bot
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ptb_app = Application.builder().token(BOT_TOKEN).build()

# --- BOT COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # 1. Supabase mein user ka data 'pending' status ke sath daalna
    try:
        supabase.table("users").upsert({
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "status": "pending"
        }).execute()
    except Exception as e:
        print(f"Supabase Insert Error: {e}")

    # 2. Google Login URL Generate karna
    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri=f"{RENDER_URL}/callback"
        )
        
        # 'state' ke zariye hum user ki Telegram ID pass karte hain
        auth_url, _ = flow.authorization_url(
            prompt='consent', 
            access_type='offline', 
            state=str(user.id)
        )
        
        keyboard = [[InlineKeyboardButton("Login with Google", url=auth_url)]]
        await update.message.reply_text(
            "Welcome! To use the Smart Email Assistant, please link your Google account.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Google Auth URL Error: {e}")
        await update.message.reply_text("Error generating login link. Check server logs.")

# YAHI WO LINE HAI JO MISSING THI
ptb_app.add_handler(CommandHandler("start", start))


# --- FASTAPI & WEBHOOK SETUP ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ptb_app.initialize()
    await ptb_app.bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    await ptb_app.start()
    yield
    await ptb_app.stop()
    await ptb_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    await ptb_app.process_update(Update.de_json(data, ptb_app.bot))
    return {"status": "ok"}

@app.get("/callback")
async def google_callback(request: Request):
    code = request.query_params.get("code")
    tg_id = request.query_params.get("state")
    
    if not code or not tg_id:
        return {"error": "Invalid callback data. Please try logging in again."}

    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri=f"{RENDER_URL}/callback"
        )
        
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Get user's email address
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        email = user_info.get("email")

        # Store tokens and email in Supabase
        token_json = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }

        supabase.table("users").update({
            "email": email,
            "auth_token": token_json
        }).eq("telegram_id", int(tg_id)).execute()

        return {"message": "Success! Your Google account is securely linked. You can close this tab and return to Telegram."}
    
    except Exception as e:
        print(f"Callback Error: {e}")
        return {"error": "An error occurred during authentication. Check server logs."}
