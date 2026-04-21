import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

# Telegram Application Setup
ptb_app = Application.builder().token(BOT_TOKEN).build()

# /start Command Logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # User details format karna
    user_info = (
        f"Aapki Details:\n"
        f"ID: {user.id}\n"
        f"First Name: {user.first_name}\n"
        f"Username: @{user.username if user.username else 'N/A'}"
    )
    
    # User ko reply bhej dena
    await update.message.reply_text(user_info)

# Command add karna
ptb_app.add_handler(CommandHandler("start", start))

# FastAPI Lifespan (Webhook Setup)
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

# FastAPI App Setup
app = FastAPI(lifespan=lifespan)

# Webhook Endpoint
@app.post(f"/{BOT_TOKEN}")
async def process_webhook(request: Request):
    req_json = await request.json()
    update = Update.de_json(req_json, ptb_app.bot)
    await ptb_app.process_update(update)
    return {"status": "ok"}
