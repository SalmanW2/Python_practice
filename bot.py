import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from supabase import create_client, Client
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://python-practice-ennb.onrender.com")

SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.readonly',
    'openid'
]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ptb_app = Application.builder().token(BOT_TOKEN).build()

# Temporary memory to store Google login sessions (Solves the Verifier Error)
oauth_sessions = {}

def get_flow():
    return Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=f"{RENDER_URL}/callback"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    try:
        supabase.table("users").upsert({
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "status": "pending"
        }).execute()
    except Exception as e:
        logging.error(f"Supabase error: {e}")

    try:
        flow = get_flow()
        auth_url, _ = flow.authorization_url(
            prompt='consent', 
            access_type='offline', 
            state=str(user.id)
        )
        
        # Save the flow object in memory so /callback can use it
        oauth_sessions[str(user.id)] = flow 
        
        keyboard = [[InlineKeyboardButton("Login with Google", url=auth_url)]]
        await update.message.reply_text(
            "Welcome! To use the Smart Email Assistant, please link your Google account.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
         logging.error(f"Link generation error: {e}")

# IMPORTANT: Command handler added back (Solves the No Reply Error)
ptb_app.add_handler(CommandHandler("start", start))

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
        return {"error": "Invalid callback data. Missing code or state."}

    # Retrieve the exact flow object saved during /start
    flow = oauth_sessions.get(tg_id)
    if not flow:
        return {"error": "Session expired or invalid. Please type /start in the bot again."}

    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        email = user_info.get("email")

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

        # Clear the memory once done
        del oauth_sessions[tg_id]

        return {"message": "Success! Your account is linked. You can close this tab and return to the Telegram bot."}
        
    except Exception as e:
        logging.error(f"Callback Error: {e}")
        return {"error": f"Authentication failed. Details: {e}"}
