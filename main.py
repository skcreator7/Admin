import asyncio
import logging
import os
from aiohttp import web
from telegram.ext import ApplicationBuilder
from commands.admin import admin_command
from filters.link_filter import filter_links
from filters.auto_delete import auto_delete_messages

# Load token from environment variable
TOKEN = os.environ.get("BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Health check endpoint
async def health_check(request):
    return web.Response(text="Bot is healthy!")

# Health check server
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)  # Port 8000 for Koyeb health check
    await site.start()
    print("Health check server running on port 8000")

# Telegram bot setup
async def start_bot():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(admin_command)
    application.add_handler(filter_links)
    application.add_handler(auto_delete_messages)

    print("Telegram bot running...")
    await application.run_polling()

# Main function
async def main():
    await asyncio.gather(
        start_bot(),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
