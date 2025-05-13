import logging
import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

class TelegramBot:
    def __init__(self):
        self.application = None
        self.runner = None
        self.site = None

    async def delete_message(self, context: ContextTypes.DEFAULT_TYPE):
        """Delete a specific message"""
        try:
            await context.bot.delete_message(
                chat_id=context.job.chat_id,
                message_id=context.job.data
            )
            logger.info(f"Deleted message {context.job.data}")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        reply = await update.message.reply_text("Hello! I'm your group management bot.")
        context.job_queue.run_once(
            self.delete_message,
            180,  # 3 minutes
            chat_id=reply.chat_id,
            data=reply.message_id,
            name=f"del_{reply.message_id}"
        )

    async def delete_unwanted_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete messages with links or mentions"""
        message = update.message
        if 'http' in message.text or '@' in message.text:
            try:
                await message.delete()
                warning = await context.bot.send_message(
                    chat_id=message.chat.id,
                    text="⚠️ Links and @usernames are not allowed!"
                )
                context.job_queue.run_once(
                    self.delete_message,
                    180,  # 3 minutes
                    chat_id=warning.chat_id,
                    data=warning.message_id,
                    name=f"del_warn_{warning.message_id}"
                )
            except Exception as e:
                logger.error(f"Message deletion error: {e}")

    async def handle_new_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Auto-delete regular user messages after 5 minutes"""
        if update.message.from_user.id not in [
            admin.user.id for admin in 
            await context.bot.get_chat_administrators(update.message.chat.id)
        ]:
            context.job_queue.run_once(
                self.delete_message,
                300,  # 5 minutes
                chat_id=update.message.chat_id,
                data=update.message.message_id,
                name=f"del_msg_{update.message.message_id}"
            )

    async def health_check(self, request):
        """Health check endpoint"""
        return web.Response(text="Bot is running")

    async def start_web_server(self):
        """Start the web server for health checks"""
        app = web.Application()
        app.router.add_get("/", self.health_check)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", 8000)
        await self.site.start()
        logger.info("Health check server running on port 8000")

    async def stop_web_server(self):
        """Stop the web server"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Web server stopped")

    async def run(self):
        """Main entry point for the bot"""
        try:
            # Initialize the bot application
            self.application = (
                ApplicationBuilder()
                .token(BOT_TOKEN)
                .concurrent_updates(True)
                .build()
            )

            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.delete_unwanted_messages)
            )
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_new_message)
            )

            # Start web server
            await self.start_web_server()

            # Run the bot until stopped
            await self.application.run_polling()

        except asyncio.CancelledError:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self):
        """Cleanup resources"""
        logger.info("Shutting down...")
        try:
            if self.application:
                if self.application.updater:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        await self.stop_web_server()
        logger.info("Shutdown complete")

async def main():
    bot = TelegramBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

if __name__ == "__main__":
    # Use asyncio.run() for proper event loop management
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped")
