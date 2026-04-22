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

# Google Scopes
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.readonly',
    'openid'
]

# Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ptb_app = Application.builder().token(BOT_TOKEN).build()

# Helper function to create Flow instance
def get_flow():
    return Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=f"{RENDER_URL}/callback"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Create or update user as pending in Supabase
    try:
        supabase.table("users").upsert({
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "status": "pending"
        }).execute()
    except Exception as e:
        logging.error(f"Supabase upsert error: {e}")

    # Generate Google Login URL
    try:
        flow = get_flow()
        # Add access_type and include_granted_scopes
        auth_url, _ = flow.authorization_url(
            prompt='consent', 
            access_type='offline', 
            include_granted_scopes='true',
            state=str(user.id) # Passing telegram ID as state
        )
        
        keyboard = [[InlineKeyboardButton("Login with Google", url=auth_url)]]
        await update.message.reply_text(
            "Welcome! To use the Smart Email Assistant, please link your Google account.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
         logging.error(f"Flow creation error: {e}")
         await update.message.reply_text("Error generating login link. Check logs.")

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

    try:
        flow = get_flow()
        # Using fetch_token with just the code, no PKCE required here for standard web flow
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

        # Update the database
        supabase.table("users").update({
            "email": email,
            "auth_token": token_json
        }).eq("telegram_id", int(tg_id)).execute()

        return {"message": "Success! Your account is linked. You can close this tab and return to the bot."}
        
    except Exception as e:
        logging.error(f"Callback Error: {e}")
        return {"error": f"An error occurred during authentication. Check server logs. Details: {e}"}
