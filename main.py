import os
import re
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Set your environment variable in Koyeb
TOKEN = os.environ.get("TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# Pattern to detect links or usernames
LINK_PATTERN = re.compile(r"(https?://\S+|t\.me/\S+|@\w+)", re.IGNORECASE)

# Check if a user is an admin
async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    member = await chat.get_member(user.id)
    return member.status in ["administrator", "creator"]

# /admin command
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_user_admin(update, context):
        await update.message.reply_text("You're an admin!")
    else:
        await update.message.reply_text("You are not an admin.")

# Handle normal messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    if LINK_PATTERN.search(message.text):
        await message.delete()
        return

    # Schedule message deletion after 5 minutes (300 seconds)
    await asyncio.sleep(300)
    try:
        await message.delete()
    except:
        pass  # Message might already be deleted

# Health check
async def health_check(request):
    return web.Response(text="OK")

async def start_bot():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Start the bot
    print("Telegram bot running...")
    await application.run_polling()

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Health check server running on port {PORT}")

async def main():
    await asyncio.gather(
        start_health_server(),
        start_bot(),
    )

if __name__ == "__main__":
    asyncio.run(main())
