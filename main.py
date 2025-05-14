import logging
import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
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
        self.stop_event = asyncio.Event()

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
        try:
            admins = await context.bot.get_chat_administrators(update.message.chat.id)
            admin_ids = [admin.user.id for admin in admins]
            
            if update.message.from_user.id not in admin_ids:
                context.job_queue.run_once(
                    self.delete_message,
                    300,  # 5 minutes
                    chat_id=update.message.chat_id,
                    data=update.message.message_id,
                    name=f"del_msg_{update.message.message_id}"
                )
        except Exception as e:
            logger.error(f"Message handling error: {e}")

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

    async def initialize_bot(self):
        """Initialize the Telegram bot application"""
        self.application = (
            Application.builder()
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

        await self.application.initialize()
        await self.application.start()
        logger.info("Bot initialized")

    async def run_polling(self):
        """Run the bot in polling mode with proper error handling"""
        try:
            while not self.stop_event.is_set():
                try:
                    await self.application.updater.start_polling()
                    await self.stop_event.wait()
                except Exception as e:
                    logger.error(f"Polling error: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")
        
        # Stop the updater if it's running
        if self.application and hasattr(self.application, 'updater'):
            try:
                await self.application.updater.stop()
            except Exception as e:
                logger.error(f"Error stopping updater: {e}")

        # Stop the application
        if self.application:
            try:
                await self.application.stop()
                await self.application.shutdown()
            except Exception as e:
                logger.error(f"Error stopping application: {e}")

        # Stop the web server
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        
        logger.info("Cleanup complete")

    async def run(self):
        """Main entry point for the bot"""
        try:
            await self.start_web_server()
            await self.initialize_bot()
            
            # Start the polling in a separate task
            polling_task = asyncio.create_task(self.run_polling())
            
            # Keep the main task running
            while not self.stop_event.is_set():
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.stop_event.set()
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
            self.stop_event.set()
        finally:
            await self.cleanup()

async def main():
    bot = TelegramBot()
    try:
        await bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    # Check if running in an environment with existing event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logger.info("Using existing event loop")
            loop.create_task(main())
        else:
            logger.info("Creating new event loop")
            asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
