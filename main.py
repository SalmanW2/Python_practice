from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN, RENDER_URL
from database import handle_new_user
from auth import get_login_url, process_callback
from admin import admin_router

# Initialize Telegram App
ptb_app = Application.builder().token(BOT_TOKEN).build()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check User Status from Database
    status = handle_new_user(user)

    if status == "pending":
        await update.message.reply_text("Aapki request admin ke paas chali gayi hai. Approve hone ka wait karein.")
    
    elif status == "blocked":
        await update.message.reply_text("Sorry, aap is bot ko use nahi kar sakte. Aapko block kiya gaya hai.")
    
    elif status == "approved":
        # System generates Login Link if approved
        auth_url = get_login_url(user.id)
        keyboard = [[InlineKeyboardButton("Login with Google", url=auth_url)]]
        await update.message.reply_text(
            "Welcome Back! Aap approved hain. Apna Google account link karein:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

ptb_app.add_handler(CommandHandler("start", start_command))

# FastAPI Lifespan for Webhooks
@asynccontextmanager
async def lifespan(app: FastAPI):
    await ptb_app.initialize()
    await ptb_app.bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    await ptb_app.start()
    yield
    await ptb_app.stop()
    await ptb_app.shutdown()

app = FastAPI(lifespan=lifespan)

# Include Admin Panel Routes
app.include_router(admin_router)

# Self-Ping Endpoint (For Cron Job)
@app.get("/ping")
async def ping():
    return {"status": "Render is Awake!"}

# Telegram Webhook Receiver
@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    await ptb_app.process_update(Update.de_json(data, ptb_app.bot))
    return {"status": "ok"}

# Google OAuth Callback
@app.get("/callback")
async def google_callback(request: Request):
    code = request.query_params.get("code")
    tg_id = request.query_params.get("state")
    
    if not code or not tg_id:
        return {"error": "Invalid Data"}

    success, message = process_callback(code, tg_id)
    return {"message": message}
