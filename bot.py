import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from supabase import create_client
import uvicorn

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def store_user(telegram_id, username):
    # Check if user exists, if not insert into pending_users
    res = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if not res.data:
        supabase.table("pending_users").insert({"telegram_id": telegram_id, "username": username}).execute()

def store_message(telegram_id, message_text):
    supabase.table("messages").insert({"telegram_id": telegram_id, "message": message_text}).execute()

async def start(update: Update, context):
    uid = update.effective_user.id
    uname = update.effective_user.username or "No username"
    store_user(uid, uname)
    await update.message.reply_text(f"✅ Your ID: {uid}\nUsername: {uname}")

async def echo(update: Update, context):
    uid = update.effective_user.id
    text = update.message.text
    store_message(uid, text)
    await update.message.reply_text(f"ID: {uid} said: {text}")

# Build Telegram app
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# FastAPI app
fastapi_app = FastAPI()

@fastapi_app.post("/webhook")
async def webhook(request: Request):
    req = await request.json()
    update = Update.de_json(req, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

@fastapi_app.get("/")
async def root():
    return {"status": "ok"}

async def set_webhook():
    # Await the coroutine
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/webhook"
    await telegram_app.bot.set_webhook(webhook_url)
    print(f"Webhook set to {webhook_url}")

if __name__ == "__main__":
    # Set webhook
    asyncio.run(set_webhook())
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(fastapi_app, host="0.0.0.0", port=port)
