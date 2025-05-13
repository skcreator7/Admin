import logging
import asyncio
import os
from aiohttp import web
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from utils import delete_later, contains_link_or_username

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update, context):
    await update.message.reply_text("Bot is online!")

async def handle_message(update, context):
    message = update.message
    if contains_link_or_username(message.text):
        await message.delete()
    else:
        asyncio.create_task(delete_later(message, delay=300))

async def health_handler(request):
    return web.Response(text="OK")

async def run_health_server():
    app = web.Application()
    app.router.add_get("/", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

async def main():
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    await asyncio.gather(
        telegram_app.run_polling(),
        run_health_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
