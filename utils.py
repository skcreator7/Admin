import re
import asyncio

async def handle_message(update, context):
    message = update.message
    text = message.text

    if re.search(r"(https?://|t\.me/|@[\w_]+)", text):
        try:
            await message.delete()
            reply = await message.reply_text("मेरे सामने होशियारी नहीं")
            await asyncio.sleep(180)
            await reply.delete()
        except Exception as e:
            print(f"Failed to handle spam message: {e}")
    else:
        try:
            await asyncio.sleep(300)  # 5 minutes
            await message.delete()
        except Exception as e:
            print(f"Failed to delete normal message: {e}")
