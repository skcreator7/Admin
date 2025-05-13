import logging
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio
from aiohttp import web

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Command to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm your group management bot.")

# Delete messages that contain links or @usernames
async def delete_unwanted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    chat_id = message.chat.id

    if 'http' in message.text or '@' in message.text:
        try:
            await message.delete()
            await context.bot.send_message(
                chat_id=chat_id,
                text="Links and @usernames are not allowed!"
            )
        except Exception as e:
            logger.error(f"Error deleting message or sending warning: {e}")

# Function to automatically delete messages after 5 minutes
async def auto_delete_messages(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    message_id = context.job.data

    try:
        await context.bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.error(f"Error auto-deleting message: {e}")

# Handle new messages from users
async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id

    admins = [admin.user.id for admin in await context.bot.get_chat_administrators(chat_id)]

    if user_id not in admins:
        context.job_queue.run_once(
            auto_delete_messages,
            when=300,
            data=message.message_id,
            chat_id=chat_id
        )

# Health check endpoint
async def health_check(request):
    return web.Response(text="OK")

# Function to run the health check server
async def run_health_check_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    logger.info("Health check server started on port 8000")
    # Keep running
    while True:
        await asyncio.sleep(3600)

# Main function to run the bot
async def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_unwanted_messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_message))

    # Start health check server as a separate task
    asyncio.create_task(run_health_check_server())

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
