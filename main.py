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
            chat_id=reply.chat_id,
            data=reply.message_id,
            name=f"del_{reply.message_id}"
        )

    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        if not message.text:  # Skip if not a text message
            return

        try:
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
                            180,
                            chat_id=warning.chat_id,
                            data=warning.message_id,
                            name=f"del_warn_{warning.message_id}"
                        )
                        return  # Skip further processing if message was deleted
                    except Exception as e:
                        logger.error(f"Immediate deletion error: {e}")
                
                # Schedule regular message deletion
                context.job_queue.run_once(
                    self.delete_message,
                    300,  # 5 minutes
                    chat_id=message.chat_id,
                    data=message.message_id,
                    name=f"del_msg_{message.message_id}"
                )
                
        except Exception as e:
            logger.error(f"Message processing error: {e}")

    # ... [keep the rest of your methods unchanged] ...

    async def initialize_bot(self):
        self.application = (
            Application.builder()
            .token(BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )

        self.application.add_handler(CommandHandler("start", self.start))
        
        # Combined message handler
        message_filter = filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE
        self.application.add_handler(
            MessageHandler(message_filter, self.process_message)
        )

        await self.application.initialize()
        await self.application.start()
        logger.info("Bot initialized")

    # ... [rest of your code remains the same] ...
