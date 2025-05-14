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

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("No BOT_TOKEN found in environment variables!")
    exit(1)

class TelegramBot:
    def __init__(self):
        self.application = None
        self.runner = None
        self.site = None
        self.stop_event = asyncio.Event()
        self.AUTO_DELETE_TIME = 180  # 3 minutes in seconds

    async def delete_message(self, context: ContextTypes.DEFAULT_TYPE):
        try:
            await context.bot.delete_message(
                chat_id=context.job.chat_id,
                message_id=context.job.data
            )
            logger.info(f"Deleted message {context.job.data}")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            reply = await update.message.reply_text(
                "Hello! I'm your group management bot. I'll auto-delete messages after 3 minutes."
            )
            context.job_queue.run_once(
                self.delete_message,
                self.AUTO_DELETE_TIME,
                chat_id=reply.chat_id,
                data=reply.message_id,
                name=f"del_{reply.message_id}"
            )
        except Exception as e:
            logger.error(f"Error in start command: {e}")

    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = update.message
            if not message or not message.text:
                return

            logger.debug(f"Processing message from {message.from_user.id} in {message.chat.id}")

            # Get admin list
            admins = await context.bot.get_chat_administrators(message.chat.id)
            admin_ids = [admin.user.id for admin in admins]
            
            # If user is not admin, process deletion
            if message.from_user.id not in admin_ids:
                # Immediate deletion for links/mentions
                if 'http' in message.text.lower() or '@' in message.text:
                    try:
                        await message.delete()
                        warning = await context.bot.send_message(
                            chat_id=message.chat.id,
                            text="⚠️ Links and @usernames are not allowed!"
                        )
                        # Schedule warning deletion
                        context.job_queue.run_once(
                            self.delete_message,
                            self.AUTO_DELETE_TIME,
                            chat_id=warning.chat_id,
                            data=warning.message_id,
                            name=f"del_warn_{warning.message_id}"
                        )
                        return
                    except Exception as e:
                        logger.error(f"Immediate deletion error: {e}")
                
                # Schedule regular message deletion
                context.job_queue.run_once(
                    self.delete_message,
                    self.AUTO_DELETE_TIME,
                    chat_id=message.chat_id,
                    data=message.message_id,
                    name=f"del_msg_{message.message_id}"
                )
                
        except Exception as e:
            logger.error(f"Message processing error: {e}", exc_info=True)

    async def health_check(self, request):
        return web.Response(text="Bot is running")

    async def start_web_server(self):
        try:
            app = web.Application()
            app.router.add_get("/", self.health_check)
            self.runner = web.AppRunner(app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, "0.0.0.0", 8000)
            await self.site.start()
            logger.info("Health check server running on port 8000")
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
            raise

    async def initialize_bot(self):
        try:
            self.application = (
                Application.builder()
                .token(BOT_TOKEN)
                .concurrent_updates(True)
                .build()
            )

            # Combined message handler
            message_filter = filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(MessageHandler(message_filter, self.process_message))

            await self.application.initialize()
            await self.application.start()
            logger.info("Bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise

    async def run_bot(self):
        try:
            logger.info("Starting bot polling...")
            await self.application.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot is now running")
            await self.stop_event.wait()
        except asyncio.CancelledError:
            logger.info("Bot shutdown requested")
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self):
        logger.info("Shutting down bot...")
        try:
            if hasattr(self, 'application') and self.application:
                if hasattr(self.application, 'updater') and self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")

        try:
            if hasattr(self, 'site') and self.site:
                await self.site.stop()
            if hasattr(self, 'runner') and self.runner:
                await self.runner.cleanup()
        except Exception as e:
            logger.error(f"Error during web server shutdown: {e}")

        logger.info("Shutdown complete")

    async def run(self):
        try:
            await self.start_web_server()
            await self.initialize_bot()
            
            # Run both tasks
            await asyncio.gather(
                self.run_bot(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Fatal error in bot: {e}", exc_info=True)
        finally:
            self.stop_event.set()
            await self.shutdown()

async def main():
    logger.info("Starting bot...")
    bot = TelegramBot()
    try:
        await bot.run()
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
    finally:
        logger.info("Application shutdown complete")
