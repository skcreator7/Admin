import logging
import os
import re
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm your group management bot.")

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

async def auto_delete_messages(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    message_id = context.job.data

    try:
        await context.bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.error(f"Error auto-deleting message: {e}")

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


def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_unwanted_messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_message))

    application.run_polling()

if __name__ == "__main__":
    main()
