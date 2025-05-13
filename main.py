import os
import re
import logging
import asyncio
from datetime import datetime, timedelta
from aiohttp import web
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# Logging setup
logging.basicConfig(level=logging.INFO)

# Bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {5928972764}  # <-- apna Telegram user ID daalo yahan

# Start command (only admin)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        await update.message.reply_text("Admin command successful.")
    else:
        await update.message.reply_text("You are not authorized.")

# Filter and delete unwanted messages
async def message_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    text = message.text.lower()
    if "http://" in text or "https://" in text or "@" in text:
        try:
            await message.delete()
        except Exception as e:
            logging.warning(f"Failed to delete message: {e}")
        return

    # Schedule auto-delete after 5 minutes
    try:
        await asyncio.sleep(300)
        await message.delete()
    except:
        pass

# Health check server (port 8080 for Koyeb)
async def handle_health(request):
    return web.Response(text="OK")

def start_health_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    loop.run_until_complete(site.start())
    logging.info("Health check server running on port 8080")

# Main function
def main():
    start_health_server()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_filter))

    logging.info("Telegram bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
