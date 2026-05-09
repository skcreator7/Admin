import random
import asyncio
import re
import os
from telethon import TelegramClient, events, types
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Bot Configuration
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Validate credentials
if not API_ID or API_ID == 0:
    logger.error("API_ID not set!")
    exit(1)

if not API_HASH:
    logger.error("API_HASH not set!")
    exit(1)

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set!")
    exit(1)

# Configuration
IMAGE_URL = "https://i.ibb.co/VYB5J028/x.jpg"
CHANNEL_LINK = "https://t.me/+0iMDc7jCLThkNmRl"
WEBSITE_LINK = "https://sk4film.vercel.app/"
APP_LINK = "https://t.me/How_to_Download_Sk/102"
AUTO_DELETE_TIME = 300

# Initialize client
client = TelegramClient('sk4film_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def delete_message_after_delay(chat_id, message_id, delay):
    """Delete message after delay"""
    try:
        await asyncio.sleep(delay)
        await client.delete_messages(chat_id, message_id)
        logger.info(f"Deleted message {message_id}")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Handle /start command"""
    try:
        await event.delete()
        
        keyboard = [
            [types.KeyboardButtonUrl(text="🟢 OFFICIAL CHANNEL", url=CHANNEL_LINK)],
            [types.KeyboardButtonUrl(text="🔵 OFFICIAL WEBSITE", url=WEBSITE_LINK)],
            [types.KeyboardButtonUrl(text="🔴 ANDROID APP", url=APP_LINK)]
        ]
        
        reply_markup = types.ReplyInlineMarkup(keyboard)
        
        caption = (
            "✨ **WELCOME TO SK4FILM BOT** ✨\n\n"
            "🎬 **Your Ultimate Entertainment Partner**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🌟 **What We Offer:**\n"
            "• 📢 Latest movie updates\n"
            "• 🎯 Exclusive content\n"
            "• 📱 Android App access\n"
            "• 💬 24/7 support\n\n"
            "👇 **Click buttons below to explore** 👇\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "_Thank you for choosing SK4Film!_ 🎉"
        )
        
        try:
            result = await client.send_file(
                event.chat_id,
                IMAGE_URL,
                caption=caption,
                parse_mode='markdown',
                reply_markup=reply_markup
            )
        except:
            result = await client.send_message(
                event.chat_id,
                caption,
                parse_mode='markdown',
                reply_markup=reply_markup
            )
            
        asyncio.create_task(
            delete_message_after_delay(event.chat_id, result.id, AUTO_DELETE_TIME)
        )
            
    except Exception as e:
        logger.error(f"Error in start: {e}")

@client.on(events.ChatAction)
async def welcome_new_members(event):
    """Welcome new members"""
    try:
        if event.user_joined or event.users_joined:
            users = event.users_joined if event.users_joined else [event.user_id]
            
            for user_id in users:
                try:
                    user = await client.get_entity(user_id)
                    
                    if user.is_self:
                        continue
                    
                    # Check if admin
                    try:
                        chat_admins = await client.get_participants(event.chat_id, filter=types.ChannelParticipantsAdmins)
                        admin_ids = [admin.id for admin in chat_admins]
                        if user.id in admin_ids:
                            continue
                    except:
                        pass
                    
                    keyboard = [
                        [types.KeyboardButtonUrl(text="🟢 JOIN CHANNEL", url=CHANNEL_LINK)],
                        [types.KeyboardButtonUrl(text="🔵 VISIT WEBSITE", url=WEBSITE_LINK)],
                        [types.KeyboardButtonUrl(text="🔴 DOWNLOAD APP", url=APP_LINK)]
                    ]
                    
                    reply_markup = types.ReplyInlineMarkup(keyboard)
                    
                    caption = (
                        f"✨ **Welcome {user.first_name}!** ✨\n\n"
                        "🎬 **SK4FILM Community**\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "⚠️ **Group Rules:**\n"
                        "• ❌ No links or @mentions\n"
                        "• ⏰ Messages auto-delete after 5 minutes\n"
                        "• 👑 Admins are exempt\n\n"
                        "👇 **Click buttons below** 👇"
                    )
                    
                    try:
                        await client.send_file(
                            event.chat_id,
                            IMAGE_URL,
                            caption=caption,
                            parse_mode='markdown',
                            reply_markup=reply_markup
                        )
                    except:
                        await client.send_message(
                            event.chat_id,
                            caption,
                            parse_mode='markdown',
                            reply_markup=reply_markup
                        )
                        
                except Exception as e:
                    logger.error(f"Error welcoming user: {e}")
                    
    except Exception as e:
        logger.error(f"Error in chat action: {e}")

@client.on(events.NewMessage)
async def process_message(event):
    """Process messages"""
    try:
        if event.is_private or event.out or (event.message.text and event.message.text.startswith('/')):
            return
        
        try:
            sender = await event.get_sender()
            if not sender:
                return
        except:
            return
        
        # Check if admin
        try:
            chat_admins = await client.get_participants(event.chat_id, filter=types.ChannelParticipantsAdmins)
            admin_ids = [admin.id for admin in chat_admins]
            is_admin = sender.id in admin_ids
        except:
            is_admin = False
        
        # Admin messages - keep
        if is_admin:
            return
        
        # Check for links
        message_text = event.message.text or ""
        has_link = bool(re.search(r'http[s]?://|www\.|t\.me/|@', message_text, re.IGNORECASE))
        
        if has_link:
            try:
                await event.delete()
                logger.info(f"Deleted link from {sender.id}")
                
                warning = await client.send_message(
                    event.chat_id,
                    "⚠️ **ACCESS DENIED!**\n\nLinks and @mentions are not allowed.\n\n_This message will self-destruct in 10 seconds._",
                    parse_mode='markdown',
                    reply_to=event.message.id
                )
                
                asyncio.create_task(
                    delete_message_after_delay(event.chat_id, warning.id, 10)
                )
                return
            except:
                pass
        
        # Schedule deletion
        asyncio.create_task(
            delete_message_after_delay(event.chat_id, event.message.id, AUTO_DELETE_TIME)
        )
        
    except Exception as e:
        logger.error(f"Error processing: {e}")

async def main():
    logger.info("🎨 SK4FILM Bot Started! 🚀")
    logger.info("✅ Auto-welcome new members - ACTIVE")
    logger.info("✅ Admin message protection - ACTIVE")
    logger.info("✅ Delete links/mentions - ACTIVE")
    logger.info("✅ Auto-delete after 5 minutes - ACTIVE")
    logger.info("✅ Styled buttons - ACTIVE")
    
    print("\n" + "="*50)
    print("🤖 SK4FILM BOT IS RUNNING SUCCESSFULLY!")
    print("="*50)
    print(f"📢 Channel: {CHANNEL_LINK}")
    print(f"🌐 Website: {WEBSITE_LINK}")
    print(f"📱 App: {APP_LINK}")
    print("="*50 + "\n")
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    # Simple run without web server
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
