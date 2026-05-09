import random
import asyncio
import re
from telethon import TelegramClient, events, types, functions
from telethon.tl.types import MessageEntityTextUrl
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Bot Configuration
API_ID = 'YOUR_API_ID'  # Get from my.telegram.org
API_HASH = 'YOUR_API_HASH'  # Get from my.telegram.org
BOT_TOKEN = 'YOUR_BOT_TOKEN'  # From @BotFather

# Image URL
IMAGE_URL = "https://i.ibb.co/VYB5J028/x.jpg"

# Channel/Group Links
CHANNEL_LINK = "https://t.me/+0iMDc7jCLThkNmRl"
WEBSITE_LINK = "https://sk4film.vercel.app/"
APP_LINK = "https://t.me/How_to_Download_Sk/102"

# Auto-delete time (5 minutes = 300 seconds)
AUTO_DELETE_TIME = 300

client = TelegramClient('sk4film_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Store message IDs for auto-deletion
messages_to_delete = {}

async def delete_message_after_delay(chat_id, message_id, delay):
    """Delete message after specified delay"""
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, message_id)
        logger.info(f"Deleted message {message_id} after {delay}s")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Handle /start command with colored buttons"""
    try:
        # Delete command message
        await event.delete()
        
        # Colored button styles
        green_style = types.KeyboardButtonStyle(
            bg_primary=True,  # Green color
            icon=5258096772776991776  # Channel icon
        )
        
        blue_style = types.KeyboardButtonStyle(
            bg_success=True,  # Blue color
            icon=5258503720928288433  # Website icon
        )
        
        red_style = types.KeyboardButtonStyle(
            bg_danger=True,  # Red color
            icon=5258331647358540449  # App icon
        )
        
        # Create colored buttons
        channel_button = types.KeyboardButtonCallback(
            text="📢 Official Channel",
            data=b"channel",
            style=green_style
        )
        
        website_button = types.KeyboardButtonCallback(
            text="🌐 Official Website",
            data=b"website",
            style=blue_style
        )
        
        app_button = types.KeyboardButtonCallback(
            text="📱 Android App",
            data=b"app",
            style=red_style
        )
        
        # Create inline markup
        markup = types.ReplyInlineMarkup(rows=[
            types.KeyboardButtonRow(buttons=[channel_button]),
            types.KeyboardButtonRow(buttons=[website_button]),
            types.KeyboardButtonRow(buttons=[app_button])
        ])
        
        # Stylish caption
        caption = (
            "✨ **WELCOME TO SK4FILM BOT** ✨\n\n"
            "🎬 **Your Ultimate Entertainment Partner**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🌟 **What We Offer:**\n"
            "• 📢 Latest movie updates\n"
            "• 🎯 Exclusive content\n"
            "• 📱 Android App access\n"
            "• 💬 24/7 support\n\n"
            "👇 **Click colored buttons below to explore** 👇\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "_Thank you for choosing SK4Film!_ 🎉"
        )
        
        # Send image with colored buttons
        try:
            result = await client.send_file(
                event.chat_id,
                IMAGE_URL,
                caption=caption,
                parse_mode='markdown',
                reply_markup=markup
            )
            
            # Schedule auto-deletion after 5 minutes
            asyncio.create_task(
                delete_message_after_delay(event.chat_id, result.id, AUTO_DELETE_TIME)
            )
            
        except Exception as e:
            logger.error(f"Error sending image: {e}")
            # Fallback: send text message
            result = await client.send_message(
                event.chat_id,
                caption,
                parse_mode='markdown',
                reply_markup=markup
            )
            asyncio.create_task(
                delete_message_after_delay(event.chat_id, result.id, AUTO_DELETE_TIME)
            )
            
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@client.on(events.ChatJoinRequest)
async def auto_approve_join_request(event):
    """Auto-approve join requests"""
    try:
        # Approve the join request
        await event.approve()
        logger.info(f"Auto-approved join request from {event.user_id}")
        
        # Send welcome message with colored buttons
        green_style = types.KeyboardButtonStyle(
            bg_primary=True,
            icon=5258096772776991776
        )
        
        blue_style = types.KeyboardButtonStyle(
            bg_success=True,
            icon=5258503720928288433
        )
        
        red_style = types.KeyboardButtonStyle(
            bg_danger=True,
            icon=5258331647358540449
        )
        
        channel_button = types.KeyboardButtonCallback(
            text="📢 Join Channel",
            data=b"channel",
            style=green_style
        )
        
        website_button = types.KeyboardButtonCallback(
            text="🌐 Visit Website",
            data=b"website",
            style=blue_style
        )
        
        app_button = types.KeyboardButtonCallback(
            text="📱 Download App",
            data=b"app",
            style=red_style
        )
        
        markup = types.ReplyInlineMarkup(rows=[
            types.KeyboardButtonRow(buttons=[channel_button]),
            types.KeyboardButtonRow(buttons=[website_button]),
            types.KeyboardButtonRow(buttons=[app_button])
        ])
        
        caption = (
            f"✨ **Welcome to SK4FILM!** ✨\n\n"
            "🎬 **Your Ultimate Entertainment Partner**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ **Group Rules:**\n"
            "• ❌ No links or @mentions\n"
            "• ⏰ Messages auto-delete after 5 minutes\n"
            "• 👑 Admins are exempt from rules\n\n"
            "👇 **Click colored buttons to explore** 👇"
        )
        
        try:
            await client.send_file(
                event.chat_id,
                IMAGE_URL,
                caption=caption,
                parse_mode='markdown',
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Error sending welcome image: {e}")
            await client.send_message(
                event.chat_id,
                caption,
                parse_mode='markdown',
                reply_markup=markup
            )
            
    except Exception as e:
        logger.error(f"Error approving join request: {e}")

@client.on(events.CallbackQuery)
async def handle_button_click(event):
    """Handle colored button clicks"""
    try:
        # Answer the callback
        if event.data == b"channel":
            await event.answer("Opening Official Channel...")
            await event.edit(
                f"📢 **Join Our Official Channel**\n\n"
                f"Click here to join: {CHANNEL_LINK}\n\n"
                f"_This message will auto-delete in 30 seconds._",
                parse_mode='markdown'
            )
            # Schedule deletion
            asyncio.create_task(
                delete_message_after_delay(event.chat_id, event.message_id, 30)
            )
            
        elif event.data == b"website":
            await event.answer("Opening Official Website...")
            await event.edit(
                f"🌐 **Visit Our Official Website**\n\n"
                f"Click here to visit: {WEBSITE_LINK}\n\n"
                f"_This message will auto-delete in 30 seconds._",
                parse_mode='markdown'
            )
            asyncio.create_task(
                delete_message_after_delay(event.chat_id, event.message_id, 30)
            )
            
        elif event.data == b"app":
            await event.answer("Getting Android App...")
            await event.edit(
                f"📱 **Download Android App**\n\n"
                f"Click here to download: {APP_LINK}\n\n"
                f"_This message will auto-delete in 30 seconds._",
                parse_mode='markdown'
            )
            asyncio.create_task(
                delete_message_after_delay(event.chat_id, event.message_id, 30)
            )
            
    except Exception as e:
        logger.error(f"Error handling callback: {e}")

@client.on(events.NewMessage)
async def process_message(event):
    """Process all messages - delete links from non-admins"""
    try:
        # Ignore commands and bot's own messages
        if event.is_private or event.out or event.message.text.startswith('/'):
            return
        
        # Get sender info
        sender = await event.get_sender()
        
        # Check if sender is admin
        try:
            chat_admins = await client.get_participants(event.chat_id, filter=types.ChannelParticipantsAdmins)
            admin_ids = [admin.id for admin in chat_admins]
            is_admin = sender.id in admin_ids
        except:
            is_admin = False
        
        # Admin messages - NEVER delete
        if is_admin:
            logger.info(f"Admin {sender.id} message - not deleting")
            return
        
        # Check for links or mentions
        message_text = event.message.text
        has_link = bool(re.search(r'http[s]?://|www\.|t\.me/|@', message_text, re.IGNORECASE))
        
        # If has link/mention, delete immediately
        if has_link:
            try:
                await event.delete()
                logger.info(f"Deleted link message from non-admin {sender.id}")
                
                # Send warning
                warning = await client.send_message(
                    event.chat_id,
                    "⚠️ **ACCESS DENIED!**\n\nLinks and @mentions are not allowed for non-admin members.\n\n_This message will self-destruct in 10 seconds._",
                    parse_mode='markdown',
                    reply_to=event.message.id
                )
                
                # Schedule warning deletion
                asyncio.create_task(
                    delete_message_after_delay(event.chat_id, warning.id, 10)
                )
                return
                
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
        
        # Schedule regular message deletion (5 minutes)
        asyncio.create_task(
            delete_message_after_delay(event.chat_id, event.message.id, AUTO_DELETE_TIME)
        )
        logger.info(f"Scheduled deletion for message {event.message.id} from non-admin")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")

@client.on(events.ChatAction)
async def member_joined(event):
    """Welcome new members who join via invite link"""
    try:
        if event.user_joined:
            user = await event.get_user()
            
            # Skip if user is admin
            try:
                chat_admins = await client.get_participants(event.chat_id, filter=types.ChannelParticipantsAdmins)
                admin_ids = [admin.id for admin in chat_admins]
                if user.id in admin_ids:
                    return
            except:
                pass
            
            # Create colored buttons
            green_style = types.KeyboardButtonStyle(bg_primary=True, icon=5258096772776991776)
            blue_style = types.KeyboardButtonStyle(bg_success=True, icon=5258503720928288433)
            red_style = types.KeyboardButtonStyle(bg_danger=True, icon=5258331647358540449)
            
            markup = types.ReplyInlineMarkup(rows=[
                types.KeyboardButtonRow(buttons=[types.KeyboardButtonCallback(text="📢 Join Channel", data=b"channel", style=green_style)]),
                types.KeyboardButtonRow(buttons=[types.KeyboardButtonCallback(text="🌐 Visit Website", data=b"website", style=blue_style)]),
                types.KeyboardButtonRow(buttons=[types.KeyboardButtonCallback(text="📱 Download App", data=b"app", style=red_style)])
            ])
            
            caption = (
                f"✨ **Welcome {user.first_name}!** ✨\n\n"
                "🎬 **SK4FILM Community**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ **Important Rules:**\n"
                "• No links or @mentions\n"
                "• Messages auto-delete after 5 minutes\n"
                "• Admins are exempt\n\n"
                "👇 **Click colored buttons below** 👇"
            )
            
            try:
                await client.send_file(
                    event.chat_id,
                    IMAGE_URL,
                    caption=caption,
                    parse_mode='markdown',
                    reply_markup=markup
                )
            except:
                await client.send_message(
                    event.chat_id,
                    caption,
                    parse_mode='markdown',
                    reply_markup=markup
                )
                
    except Exception as e:
        logger.error(f"Error in member joined handler: {e}")

print("🎨 SK4FILM Bot with True Colored Buttons Started! 🚀")
print("✅ Auto-approve join requests - ACTIVE")
print("✅ Admin message protection - ACTIVE")
print("✅ Delete links from non-admins - ACTIVE")
print("✅ Auto-delete after 5 minutes - ACTIVE")
print("✅ True colored buttons - ACTIVE (Green, Blue, Red)")

client.run_until_disconnected()
