import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from supabase import create_client
import uvicorn

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Helper functions
def user_exists(telegram_id):
    res = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    return len(res.data) > 0

def add_pending(telegram_id, username):
    supabase.table("pending_users").insert({"telegram_id": telegram_id, "username": username}).execute()

def store_message(telegram_id, message_text):
    supabase.table("messages").insert({"telegram_id": telegram_id, "message": message_text}).execute()

# Bot handlers
async def start(update: Update, context):
    uid = update.effective_user.id
    uname = update.effective_user.username or "No username"
    if user_exists(uid):
        await update.message.reply_text("✅ Welcome back! Use /help")
    else:
        add_pending(uid, uname)
        await update.message.reply_text("⏳ Request sent to admin. Wait for approval.")

async def help_command(update: Update, context):
    await update.message.reply_text("Commands:\n/start - Check status\n/help - This message")

async def echo(update: Update, context):
    user_id = update.effective_user.id
    user_text = update.message.text
    store_message(user_id, user_text)
    await update.message.reply_text(f"You said: {user_text}")

# Create Telegram Application
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
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
    return {"status": "Bot is running with webhooks"}

if __name__ == "__main__":
    # Set webhook on startup (only once, but Render restarts often)
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/webhook"
    telegram_app.bot.set_webhook(webhook_url)
    print(f"Webhook set to {webhook_url}")
    
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(fastapi_app, host="0.0.0.0", port=port)
