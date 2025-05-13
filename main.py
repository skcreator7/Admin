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
    JobQueue,
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

class AutoDeleteBot:
    def __init__(self):
        self.application = None
        self.health_server = None
        self.active_deletions = set()  # Track active deletion jobs

    async def delete_message_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Job to delete a specific message"""
        try:
            chat_id = context.job.chat_id
            message_id = context.job.data
            
            if (chat_id, message_id) not in self.active_deletions:
                return
                
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )
            logger.info(f"Deleted message {message_id} in chat {chat_id}")
            
            # Remove from active deletions
            self.active_deletions.remove((chat_id, message_id))
            
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            # Retry in 30 seconds if failed
            await asyncio.sleep(30)
            if (chat_id, message_id) in self.active_deletions:
                context.job_queue.run_once(
                    self.delete_message_job,
                    0,  # Run immediately
                    chat_id=chat_id,
                    data=message_id,
                    name=f"retry_del_{message_id}"
                )

    async def schedule_deletion(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int):
        """Schedule a message for deletion"""
        job_name = f"del_{chat_id}_{message_id}"
        
        # Cancel any existing job for this message
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()
        
        # Track this deletion
        self.active_deletions.add((chat_id, message_id))
        
        # Schedule new deletion
        context.job_queue.run_once(
            self.delete_message_job,
            delay,
            chat_id=chat_id,
            data=message_id,
            name=job_name
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            reply = await update.message.reply_text("Hello! I'm your group management bot.")
            await self.schedule_deletion(context, reply.chat_id, reply.message_id, 180)  # 3 minutes
        except Exception as e:
            logger.error(f"Start command error: {e}")

    async def delete_unwanted_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete messages with links or mentions"""
        try:
            message = update.message
            if 'http' in message.text or '@' in message.text:
                await message.delete()
                warning = await context.bot.send_message(
                    chat_id=message.chat.id,
                    text="⚠️ Links and @usernames are not allowed!"
                )
                await self.schedule_deletion(context, warning.chat_id, warning.message_id, 180)  # 3 minutes
        except Exception as e:
            logger.error(f"Message deletion error: {e}")

    async def handle_new_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Auto-delete regular user messages after 5 minutes"""
        try:
            admins = await context.bot.get_chat_administrators(update.message.chat.id)
            admin_ids = [admin.user.id for admin in admins]
            
            if update.message.from_user.id not in admin_ids:
                await self.schedule_deletion(
                    context,
                    update.message.chat_id,
                    update.message.message_id,
                    300  # 5 minutes
                )
        except Exception as e:
            logger.error(f"Message handling error: {e}")

    async def health_check(self, request):
        """Health check endpoint"""
        return web.Response(
            text=f"Bot is running\nActive deletions: {len(self.active_deletions)}"
        )

    async def start_health_server(self):
        """Start health check server"""
        app = web.Application()
        app.router.add_get("/", self.health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8000)
        await site.start()
        logger.info("Health check server running on port 8000")
        return runner

    async def run_bot(self):
        """Initialize and run the bot"""
        self.application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .concurrent_updates(True)
            .post_init(self.on_bot_start)
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
        
        # Start services
        self.health_server = await self.start_health_server()
        await self.application.run_polling()

    async def on_bot_start(self, application):
        """Callback when bot starts"""
        logger.info("Bot has started polling for updates")
        
        # Schedule periodic job to keep the event loop active
        application.job_queue.run_repeating(
            self.keep_alive,
            interval=300,  # 5 minutes
            first=10,
            name="keep_alive"
        )

    async def keep_alive(self, context: ContextTypes.DEFAULT_TYPE):
        """Periodic job to keep bot active"""
        logger.debug("Bot keep-alive ping")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")
        if self.health_server:
            await self.health_server.cleanup()
        if self.application:
            await self.application.shutdown()

async def main():
    bot = AutoDeleteBot()
    try:
        await bot.run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        await bot.cleanup()
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    # Make sure to install with: pip install "python-telegram-bot[job-queue]"
    asyncio.run(main())
