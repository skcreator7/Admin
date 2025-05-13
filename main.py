import logging
import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def delete_message(context: ContextTypes.DEFAULT_TYPE):
    """Delete a specific message"""
    try:
        await context.bot.delete_message(
            chat_id=context.job.chat_id,
            message_id=context.job.data
        )
        logger.info(f"Successfully deleted message {context.job.data}")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    try:
        reply = await update.message.reply_text("Hello! I'm @Sk4Film management bot.")
        # Schedule deletion after 3 minutes (180 seconds)
        context.job_queue.run_once(
            delete_message,
            180,
            chat_id=reply.chat_id,
            data=reply.message_id,
            name=f"del_{reply.message_id}"
        )
    except Exception as e:
        logger.error(f"Error in start handler: {e}")

async def delete_unwanted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete messages with links or mentions"""
    try:
        message = update.message
        if 'http' in message.text or '@' in message.text:
            await message.delete()
            warning = await context.bot.send_message(
                chat_id=message.chat.id,
                text="⚠️ @Sk4Film मेरे सामने होशियारी नहीं राजा"
            )
            # Schedule warning deletion after 3 minutes
            context.job_queue.run_once(
                delete_message,
                180,
                chat_id=warning.chat_id,
                data=warning.message_id,
                name=f"del_warn_{warning.message_id}"
            )
    except Exception as e:
        logger.error(f"Error in delete_unwanted_messages: {e}")

async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-delete regular user messages after 5 minutes"""
    try:
        if update.message.from_user.id not in [admin.user.id for admin in 
                                            await context.bot.get_chat_administrators(update.message.chat.id)]:
            context.job_queue.run_once(
                delete_message,
                300,  # 5 minutes
                chat_id=update.message.chat_id,
                data=update.message.message_id,
                name=f"del_msg_{update.message.message_id}"
            )
    except Exception as e:
        logger.error(f"Error in handle_new_message: {e}")

async def health_check(request):
    return web.Response(text="OK")

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    logger.info("Health check server running on port 8000")
    return runner

async def run_bot():
    # Initialize with job queue support
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)  # Important for handling multiple messages
        .build()
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_unwanted_messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_message))
    
    # Start polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("Bot is running and polling...")
    return application

async def main():
    health_server = None
    bot = None
    
    try:
        # Start both services
        health_server = await start_health_server()
        bot = await run_bot()
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
            
    except asyncio.CancelledError:
        logger.info("Shutdown requested...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        if bot:
            await bot.updater.stop()
            await bot.stop()
            await bot.shutdown()
        if health_server:
            await health_server.cleanup()
        logger.info("Services stopped")

if __name__ == "__main__":
    # Make sure to install with: pip install "python-telegram-bot[job-queue]"
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
