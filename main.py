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

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm your group management bot.")

async def delete_unwanted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if 'http' in message.text or '@' in message.text:
        try:
            await message.delete()
            await context.bot.send_message(
                chat_id=message.chat.id,
                text="Links and @usernames are not allowed!"
            )
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in [admin.user.id for admin in 
                                         await context.bot.get_chat_administrators(update.message.chat.id)]:
        context.job_queue.run_once(
            lambda ctx: ctx.bot.delete_message(ctx.job.chat_id, ctx.job.data),
            300,
            data=update.message.message_id,
            chat_id=update.message.chat.id
        )

# Health Check Server
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
    
    # Add handlers
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
        # Start both services
        health_server = await start_health_server()
        bot = await run_bot()
        
        # Keep running forever
        while True:
            await asyncio.sleep(3600)
            
    except asyncio.CancelledError:
        logger.info("Shutting down...")
    finally:
        # Cleanup
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
