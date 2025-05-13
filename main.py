import asyncio
import os
import threading
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from utils import handle_message
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")

# Health check handler
async def health(request):
    return web.Response(text="Healthy")

# Function to run aiohttp web server
def start_health_server():
    app = web.Application()
    app.router.add_get("/", health)
    web.run_app(app, port=8080)

# Function to start the telegram bot
async def start_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    await application.run_polling()

if __name__ == "__main__":
    # Start aiohttp health server in a separate thread
    threading.Thread(target=start_health_server, daemon=True).start()

    # Run bot in main thread
    asyncio.run(start_bot())
