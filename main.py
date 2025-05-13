import logging
import asyncio
from aiohttp import web
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from utils import delete_later, contains_link_or_username
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Telegram Handlers
async def start(update, context):
    await update.message.reply_text("Bot is online!")

async def handle_message(update, context):
    message = update.message
    if contains_link_or_username(message.text):
        await message.delete()
    else:
        asyncio.create_task(delete_later(message, delay=300))  # 5 min

# Health Check
async def health(request):
    return web.Response(text="OK")

# Run aiohttp server for health check
async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

# Main
async def main():
    await start_health_server()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is running...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
