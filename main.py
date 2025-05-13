from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import logging
import re
import asyncio
from aiohttp import web

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your bot token from environment
TOKEN = os.environ.get("BOT_TOKEN")

# Simple admin check
ADMIN_IDS = [123456789]  # Replace with your Telegram user ID

# Warn counter
warn_count = {}

# Delete messages with links/usernames
async def filter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if re.search(r"(t\.me|http[s]?://|@[\w_]+)", update.message.text, re.IGNORECASE):
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")
    else:
        # Auto delete all messages after 5 minutes
        await asyncio.sleep(300)
        try:
            await update.message.delete()
        except:
            pass

# /warn command
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user to warn them.")
        return

    user_id = update.message.reply_to_message.from_user.id
    warn_count[user_id] = warn_count.get(user_id, 0) + 1
    count = warn_count[user_id]

    await update.message.reply_text(f"User warned. Total warnings: {count}")

    if count >= 3:
        await update.message.reply_text("User muted for repeated violations.")

# /admin command
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        await update.message.reply_text("You are an admin.")
    else:
        await update.message.reply_text("You are not an admin.")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running.")

# Health check endpoint
async def health_check(request):
    return web.Response(text="OK")

def run_health_server():
    app = web.Application()
    app.add_routes([web.get("/", health_check)])
    web.run_app(app, port=8080)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_message))

    # Start web server for health checks in background
    asyncio.get_event_loop().create_task(asyncio.to_thread(run_health_server))

    print("Telegram bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
