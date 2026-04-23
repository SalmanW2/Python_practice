import asyncio
import httpx
import logging
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
        await update.message.reply_text("⛔ Sorry, your access to this bot has been restricted. You are blocked.")
    elif status == "pending":
        await update.message.reply_text("⏳ Your access request has been sent to the administrator. Please wait for approval.")
    elif status == "approved":
        auth_url = get_login_url(user.id)
        keyboard = [[InlineKeyboardButton("🔗 Login with Google", url=auth_url)]]
        await update.message.reply_text(
            "✅ Welcome! Your access is approved. Please link your Google account below to proceed:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if logout_user(user.id):
        await update.message.reply_text("✅ You have successfully logged out. To use the bot again, send /start.")
    else:
        await update.message.reply_text("❌ You are already logged out or no data exists.")

ptb_app.add_handler(CommandHandler("start", start_command))
ptb_app.add_handler(CommandHandler("logout", logout_command))

async def keep_awake():
    """Background task to ping the server every 14 minutes to prevent sleep on free tier."""
    url = f"{RENDER_URL}/ping"
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(14 * 60) # 14 minutes
            try:
                await client.get(url)
                logging.info("Anti-sleep ping sent successfully.")
            except Exception as e:
                logging.error(f"Anti-sleep ping failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Webhook Initialization
    await ptb_app.initialize()
    await ptb_app.bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    await ptb_app.start()
    
    # Start anti-sleep background process
    ping_task = asyncio.create_task(keep_awake())
    
    yield
    
    # Graceful Shutdown
    ping_task.cancel()
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

    status_type, result_data = process_callback(code, state_uuid)
    
    # Route: Admin Login Success
    if status_type == "admin":
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(key="admin_session", value=result_data, max_age=86400)
        return response
        
    # Route: Admin Login Failed (Unauthorized Email)
    elif status_type == "error" and "Admin" in result_data:
        return RedirectResponse(url=f"/callback_success?msg={result_data}&success=false&is_admin_error=true")
        
    # Route: User Login Success
    elif status_type == "user":
        return RedirectResponse(url=f"/callback_success?msg={result_data}&success=true")
        
    # Route: Standard Errors
    else:
        return RedirectResponse(url=f"/callback_success?msg={result_data}&success=false")