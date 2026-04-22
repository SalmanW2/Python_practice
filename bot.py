import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from supabase import create_client, Client

# Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase aur Telegram Setup
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ptb_app = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Supabase mein data save karna (upsert se duplicate bach jayega)
    data = {
        "telegram_id": user.id,
        "username": user.username,
        "first_name": user.first_name
    }
    
    try:
        supabase.table('users').upsert(data).execute()
    except Exception as e:
        print(f"Supabase Error: {e}")

    # User ko reply
    user_info = (
        f"Aapki Details Database me save ho gayi hain!\n"
        f"ID: {user.id}\n"
        f"Name: {user.first_name}\n"
        f"Username: @{user.username if user.username else 'N/A'}"
    )
    await update.message.reply_text(user_info)

ptb_app.add_handler(CommandHandler("start", start))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ptb_app.initialize()
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
        await ptb_app.bot.set_webhook(url=webhook_url)
    await ptb_app.start()
    yield
    await ptb_app.stop()
    await ptb_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post(f"/{BOT_TOKEN}")
async def process_webhook(request: Request):
    req_json = await request.json()
    update = Update.de_json(req_json, ptb_app.bot)
    await ptb_app.process_update(update)
    return {"status": "ok"}
