import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from supabase import create_client

load_dotenv("config.env")

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
    supabase.table("messages").insert({
        "telegram_id": telegram_id,
        "message": message_text
    }).execute()

# Bot handlers
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
    
    # Store in database
    store_message(user_id, user_text)
    
    # Send back same text
    await update.message.reply_text(f"You said: {user_text}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
