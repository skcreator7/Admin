import os
import asyncio
from aiohttp import web
from telegram.ext import ApplicationBuilder
from utils import setup_handlers

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Health check endpoint
async def health_check(request):
    return web.Response(text="Healthy")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Health check server running on port 8080")

async def start_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    setup_handlers(application)
    
    print("Telegram bot running...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Keep running
    await asyncio.Event().wait()

async def main():
    await asyncio.gather(
        start_web_server(),
        start_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())
