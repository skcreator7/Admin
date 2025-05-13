import logging
import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Global dictionary to track bot's sent messages
bot_messages = {}

async def delete_bot_message(context: ContextTypes.DEFAULT_TYPE):
    """Delete a bot message after delay"""
    try:
        chat_id = context.job.data['chat_id']
        message_id = context.job.data['message_id']
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Deleted bot message {message_id} in chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to delete bot message: {e}")

async def schedule_bot_message_deletion(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
    """Schedule a bot message for deletion after 3 minutes (180 seconds)"""
    context.job_queue.run_once(
        delete_bot_message,
        180,  # 3 minutes in seconds
        data={'chat_id': chat_id, 'message_id': message_id},
        name=f"delete_{chat_id}_{message_id}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    reply = await update.message.reply_text("Hello! I'm @Sk4Film management bot.")
    await schedule_bot_message_deletion(context, reply.chat_id, reply.message_id)

async def delete_unwanted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete messages with links or mentions"""
    message = update.message
    if 'http' in message.text or '@' in message.text:
        try:
            await message.delete()
            warning = await context.bot.send_message(
                chat_id=message.chat.id,
                text="@Sk4Film मेरे सामने होशियारी नहीं राजा"
            )
            await schedule_bot_message_deletion(context, warning.chat_id, warning.message_id)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-delete regular user messages after 5 minutes"""
    if update.message.from_user.id not in [admin.user.id for admin in 
                                         await context.bot.get_chat_administrators(update.message.chat.id)]:
        context.job_queue.run_once(
            delete_bot_message,
            300,  # 5 minutes
            data={'chat_id': update.message.chat_id, 'message_id': update.message.message_id},
            name=f"delete_user_msg_{update.message.message_id}"
        )

async def health_check(request):
    return web.Response(text="OK")

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 8000).start()
    logger.info("Health check server running on port 8000")
    return runner

async def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_unwanted_messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_message))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("Bot is running and polling...")
    return application

async def main():
    health_server = None
    bot = None
    
    try:
        health_server = await start_health_server()
        bot = await run_bot()
        
        while True:
            await asyncio.sleep(3600)
            
    except asyncio.CancelledError:
        logger.info("Shutting down...")
    finally:
        if bot:
            await bot.updater.stop()
            await bot.stop()
            await bot.shutdown()
        if health_server:
            await health_server.cleanup()
        logger.info("Services stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
