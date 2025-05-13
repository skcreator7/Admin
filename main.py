import os
import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from utils import delete_later, contains_link_or_username
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

async def start(update, context):
    await update.message.reply_text("Bot is online!")

async def handle_message(update, context):
    message = update.message
    if contains_link_or_username(message.text):
        await message.delete()
    else:
        asyncio.create_task(delete_later(message, 300))

async def health_check(request):
    return web.Response(text="OK")

async def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.initialize()
    await app.start()
    logging.info("Telegram bot running...")
    await app.updater.start_polling()
    await app.updater.idle()

async def start_web():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    logging.info("Health check server running...")

async def main():
    await asyncio.gather(start_bot(), start_web())

if __name__ == "__main__":
    asyncio.run(main())
