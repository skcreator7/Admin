import os
import logging
import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Config
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [123456789]  # Replace with actual admin ID

if not TOKEN:
    logger.error("BOT_TOKEN is not set in environment variables.")
    exit(1)

# Filters
def contains_username_or_link(text: str) -> bool:
    return bool(re.search(r'@\w+|https?://\S+', text))

# Handlers
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    await update.message.reply_text("Admin command executed.")

async def message_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        if contains_username_or_link(update.message.text):
            try:
                await update.message.delete()
                logger.info("Message containing username or link deleted.")
            except Exception as e:
                logger.warning(f"Failed to delete message: {e}")
            return
        # Auto-delete after 5 mins
        await context.application.create_task(
            delete_after_delay(update.message, 300)
        )

async def delete_after_delay(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
        logger.info("Message deleted after delay.")
    except Exception as e:
        logger.warning(f"Failed to delete message after delay: {e}")

# Start Bot
async def start_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_filter))

    logger.info("Bot is starting...")
    await app.run_polling()

async def main():
    try:
        await start_bot()
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
