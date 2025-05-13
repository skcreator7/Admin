import logging
import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from aiohttp import web
from utils import contains_link_or_username, delete_later

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online!")

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message and contains_link_or_username(message.text):
        await message.delete()
    else:
        asyncio.create_task(delete_later(message, 300))

# Health check HTTP endpoint
async def health(request):
    return web.Response(text="OK")

# aiohttp server for health checks
async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

# Main bot function
async def main():
    await start_health_server()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
