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

load_dotenv()

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
        try:
            await context.bot.delete_message(
                chat_id=context.job.chat_id,
                message_id=context.job.data
            )
            logger.info(f"Deleted message {context.job.data}")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        reply = await update.message.reply_text("Hello! I'm your group management bot.")
        context.job_queue.run_once(
            self.delete_message,
            180,
            chat_id=reply.chat.id,
            data=reply.message_id,
            name=f"del_{reply.message_id}"
        )

    async def handle_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Check for unwanted content
            if 'http' in update.message.text or '@' in update.message.text:
                await update.message.delete()
                warning = await context.bot.send_message(
                    chat_id=update.message.chat.id,
                    text="⚠️ Links and @usernames are not allowed!"
                )
                context.job_queue.run_once(
                    self.delete_message,
                    180,
                    chat_id=warning.chat.id,
                    data=warning.message_id,
                    name=f"del_warn_{warning.message_id}"
                )
                return

            # Handle auto-deletion of regular user messages
            admins = await context.bot.get_chat_administrators(update.message.chat.id)
            admin_ids = [admin.user.id for admin in admins]

            if update.message.from_user.id not in admin_ids:
                context.job_queue.run_once(
                    self.delete_message,
                    300,
                    chat_id=update.message.chat.id,
                    data=update.message.message_id,
                    name=f"del_msg_{update.message.message_id}"
                )
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def health_check(self, request):
        return web.Response(text="Bot is running")

    async def start_web_server(self):
        app = web.Application()
        app.router.add_get("/", self.health_check)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", 8000)
        await self.site.start()
        logger.info("Health check server running on port 8000")

    def initialize_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_messages)
        )

    async def initialize_bot(self):
        self.application = (
            Application.builder()
            .token(BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )
        self.initialize_handlers()
        await self.application.initialize()
        await self.application.start()
        logger.info("Bot initialized")

    async def cleanup(self):
        logger.info("Cleaning up resources...")
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        logger.info("Cleanup complete")

    async def run(self):
        try:
            await self.start_web_server()
            await self.initialize_bot()
            while not self.stop_event.is_set():
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
        finally:
            self.stop_event.set()
            await self.cleanup()

async def main():
    bot = TelegramBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
    finally:
        logger.info("Application shutdown complete")
