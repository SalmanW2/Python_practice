from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN, RENDER_URL
from database import handle_user_start, logout_user
from auth import get_login_url, process_callback
from frontend import frontend_router

ptb_app = Application.builder().token(BOT_TOKEN).build()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    status = handle_user_start(user)

    if status == "blocked":
        await update.message.reply_text("⛔ Sorry, aap is bot ko use nahi kar sakte. Aapko block kiya gaya hai.")
    elif status == "pending":
        await update.message.reply_text("⏳ Aapki request admin ke paas chali gayi hai. Account approve (is_verified) hone ka wait karein.")
    elif status == "approved":
        auth_url = get_login_url(user.id)
        keyboard = [[InlineKeyboardButton("🔗 Login with Google", url=auth_url)]]
        await update.message.reply_text(
            "✅ Welcome Back! Aap approved hain. Apna Google account link karein:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if logout_user(user.id):
        await update.message.reply_text("✅ Aap successfully logout ho gaye hain. Dobara login karne ke liye /start bhejein.")
    else:
        await update.message.reply_text("❌ Aap pehle se hi logged out hain ya data exist nahi karta.")

ptb_app.add_handler(CommandHandler("start", start_command))
ptb_app.add_handler(CommandHandler("logout", logout_command))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ptb_app.initialize()
    await ptb_app.bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    await ptb_app.start()
    yield
    await ptb_app.stop()
    await ptb_app.shutdown()

app = FastAPI(lifespan=lifespan)
app.include_router(frontend_router)

@app.get("/ping")
async def ping():
    return {"status": "Render is Awake!"}

@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    await ptb_app.process_update(Update.de_json(data, ptb_app.bot))
    return {"status": "ok"}

@app.get("/callback")
async def google_callback(request: Request):
    code = request.query_params.get("code")
    state_uuid = request.query_params.get("state")
    
    if not code or not state_uuid:
        return RedirectResponse(url=f"/callback_success?msg=Invalid Request&success=false")

    success, message = process_callback(code, state_uuid)
    return RedirectResponse(url=f"/callback_success?msg={message}&success={str(success).lower()}")
