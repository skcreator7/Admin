from telegram.ext import CommandHandler, MessageHandler, filters
import re
from datetime import datetime, timedelta
import asyncio

# Delete messages with links or usernames
async def delete_links(update, context):
    if re.search(r"(t\.me|http[s]?://|@[\w_]+)", update.message.text, re.IGNORECASE):
        try:
            await update.message.delete()
        except Exception as e:
            print("Failed to delete message:", e)

# Auto-delete messages after 5 minutes
async def auto_delete(update, context):
    try:
        await asyncio.sleep(300)  # 5 minutes
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    except Exception as e:
        print("Failed to auto-delete:", e)

# Admin-only command
async def admin_only(update, context):
    user = update.effective_user
    chat = update.effective_chat
    member = await chat.get_member(user.id)
    if member.status in ['administrator', 'creator']:
        await update.message.reply_text("You're an admin.")
    else:
        await update.message.reply_text("You must be an admin to use this command.")

def setup_handlers(app):
    app.add_handler(CommandHandler("admin", admin_only))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_links))
    app.add_handler(MessageHandler(filters.ALL, auto_delete))
