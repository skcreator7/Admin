import asyncio
import os
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from utils import handle_message
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")

async def health(request):
    return web.Response(text="Healthy")

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Health check route
    app = web.Application()
    app.router.add_get("/", health)

    # Run both bot and web server
    async def run():
        print("Bot is running...")
        await asyncio.gather(
            application.run_polling(),
            web._run_app(app, port=8080)
        )

    await run()

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
        else:
            raise
