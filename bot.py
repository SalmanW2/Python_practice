import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from supabase import create_client
from fastapi import FastAPI, Request
import uvicorn

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()

def user_exists(telegram_id):
    res = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    return len(res.data) > 0

def add_pending(telegram_id, username):
    supabase.table("pending_users").insert({"telegram_id": telegram_id, "username": username}).execute()

def store_message(telegram_id, message_text):
    supabase.table("messages").insert({"telegram_id": telegram_id, "message": message_text}).execute()

async def start(update, context):
    uid = update.effective_user.id
    uname = update.effective_user.username or "No username"
    if user_exists(uid):
        await update.message.reply_text("✅ Welcome back! Use /help to see commands.")
    else:
        add_pending(uid, uname)
        await update.message.reply_text("⏳ Your request has been sent to admin. Wait for approval.")

async def help_command(update, context):
    await update.message.reply_text("Commands:\n/start - Check status\n/help - This message")

async def echo(update, context):
    user_id = update.effective_user.id
    user_text = update.message.text
    store_message(user_id, user_text)
    await update.message.reply_text(f"You said: {user_text}")

# Telegram bot setup
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# FastAPI routes
@app.post("/webhook")
async def webhook(request: Request):
    req = await request.json()
    await telegram_app.process_update(req)
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # Set webhook
    webhook_url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/webhook"
    telegram_app.bot.set_webhook(webhook_url)
    # Start FastAPI
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
