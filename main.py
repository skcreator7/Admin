import logging
import asyncio
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from utils import delete_later, contains_link_or_username
import os
from aiohttp import web

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

async def health(request):
    return web.Response(text="OK")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    runner = web.AppRunner(web.Application())
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
