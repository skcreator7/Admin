import re
import asyncio

def contains_link_or_username(text):
    if not text:
        return False
    link_pattern = re.compile(r"https?://\S+|www\.\S+")
    username_pattern = re.compile(r"@\w+")
    return bool(link_pattern.search(text) or username_pattern.search(text))

async def delete_later(message, delay=300):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass
