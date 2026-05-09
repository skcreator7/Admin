import os
import asyncio
import re
from kurigram import Client, filters
from kurigram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from kurigram.enums import ChatMemberStatus
from kurigram.types.inline_keyboard_button import ButtonStyle
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
if not API_ID or API_ID == 0 or not API_HASH or not BOT_TOKEN:
    logger.error("Missing API credentials!")
    exit(1)

# Configuration
IMAGE_URL = "https://i.ibb.co/VYB5J028/x.jpg"
OFFICIAL_LINK = "https://t.me/+0iMDc7jCLThkNmRl"
MOVIES_LINK = "https://sk4film.vercel.app/"
ANDROID_LINK = "https://t.me/How_to_Download_Sk/102"
AUTO_DELETE_TIME = 300

# Initialize Kurigram Client
app = Client("sk4film_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Custom emoji IDs (optional - requires Telegram Premium for custom emoji)
# These are default Telegram emoji IDs, replace with your custom emoji IDs
CUSTOM_EMOJI_IDS = {
    "official": 5258096772776991776,  # Example: Channel emoji
    "movies": 5258503720928288433,    # Example: Movies emoji
    "android": 5258331647358540449    # Example: Android emoji
}

async def delete_message_after_delay(chat_id, message_id, delay):
    """Delete message after delay"""
    try:
        await asyncio.sleep(delay)
        await app.delete_messages(chat_id, message_id)
        logger.info(f"Deleted message {message_id}")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Handle /start command with colored buttons"""
    try:
        await message.delete()
        
        # Create colored buttons with styles and custom emoji
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="📢 Official Channel",
                    callback_data="official_btn",
                    style=ButtonStyle.PRIMARY,  # Dark Blue
                    # icon_custom_emoji_id=CUSTOM_EMOJI_IDS["official"]  # Uncomment for custom emoji
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎬 Movies Website",
                    callback_data="movies_btn",
                    style=ButtonStyle.SUCCESS,  # Green
                    # icon_custom_emoji_id=CUSTOM_EMOJI_IDS["movies"]
                )
            ],
            [
                InlineKeyboardButton(
                    text="📱 Android App",
                    callback_data="android_btn",
                    style=ButtonStyle.DANGER,   # Red
                    # icon_custom_emoji_id=CUSTOM_EMOJI_IDS["android"]
                )
            ]
        ])
        
        caption = (
            "✨ **WELCOME TO SK4FILM BOT** ✨\n\n"
            "🎬 **Your Ultimate Entertainment Partner**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🌟 **Choose an option below:**\n\n"
            "🔵 **Official Channel** - Get latest updates\n"
            "🟢 **Movies Website** - Browse exclusive content\n"
            "🔴 **Android App** - Download & install\n\n"
            "👇 **Click colored buttons below** 👇\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "_Thank you for choosing SK4Film!_ 🎉"
        )
        
        try:
            # Send image with colored buttons
            msg = await message.reply_photo(
                photo=IMAGE_URL,
                caption=caption,
                parse_mode="markdown",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending image: {e}")
            # Fallback to text message
            msg = await message.reply_text(
                caption,
                parse_mode="markdown",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        
        # Schedule auto-deletion
        asyncio.create_task(
            delete_message_after_delay(message.chat.id, msg.id, AUTO_DELETE_TIME)
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@app.on_message(filters.command("colors"))
async def demo_colored_buttons(client, message):
    """Demo command to showcase colored buttons"""
    try:
        # Demo keyboard with all styles
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="🔵 Primary Button",
                    callback_data="demo_primary",
                    style=ButtonStyle.PRIMARY
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟢 Success Button",
                    callback_data="demo_success",
                    style=ButtonStyle.SUCCESS
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔴 Danger Button",
                    callback_data="demo_danger",
                    style=ButtonStyle.DANGER
                )
            ]
        ])
        
        await message.reply_text(
            "🎨 **Button Style Demo**\n\n"
            "🔵 **PRIMARY** - Dark Blue (Official/Channel)\n"
            "🟢 **SUCCESS** - Green (Website/Links)\n"
            "🔴 **DANGER** - Red (App/Downloads)\n\n"
            "_Click any button to test!_",
            parse_mode="markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in demo: {e}")

@app.on_chat_join_request()
async def auto_approve_join_request(client, join_request):
    """Auto approve join requests with colored buttons"""
    try:
        await join_request.approve()
        logger.info(f"Auto-approved join request from {join_request.from_user.id}")
        
        # Send welcome message with colored buttons
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="🔵 Official Channel",
                    callback_data="official_btn",
                    style=ButtonStyle.PRIMARY
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟢 Movies Website",
                    callback_data="movies_btn",
                    style=ButtonStyle.SUCCESS
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔴 Android App",
                    callback_data="android_btn",
                    style=ButtonStyle.DANGER
                )
            ]
        ])
        
        caption = (
            f"✨ **Welcome {join_request.from_user.first_name}!** ✨\n\n"
            "🎬 **SK4FILM Community**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ **Group Rules:**\n"
            "• ❌ No links or @mentions\n"
            "• ⏰ Messages auto-delete after 5 minutes\n"
            "• 👑 Admins are exempt from rules\n\n"
            "👇 **Click colored buttons below** 👇"
        )
        
        try:
            await client.send_photo(
                chat_id=join_request.chat.id,
                photo=IMAGE_URL,
                caption=caption,
                parse_mode="markdown",
                reply_markup=keyboard
            )
        except:
            await client.send_message(
                chat_id=join_request.chat.id,
                text=caption,
                parse_mode="markdown",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"Error in auto-approve: {e}")

@app.on_message(filters.new_chat_members)
async def welcome_new_members(client, message):
    """Welcome new members with colored buttons"""
    try:
        for new_member in message.new_chat_members:
            if new_member.id == client.me.id:
                continue
            
            # Check if admin
            try:
                chat_member = await client.get_chat_member(message.chat.id, new_member.id)
                if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    continue
            except:
                pass
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        text="🔵 Official Channel",
                        callback_data="official_btn",
                        style=ButtonStyle.PRIMARY
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🟢 Movies Website",
                        callback_data="movies_btn",
                        style=ButtonStyle.SUCCESS
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔴 Android App",
                        callback_data="android_btn",
                        style=ButtonStyle.DANGER
                    )
                ]
            ])
            
            caption = (
                f"✨ **Welcome {new_member.first_name}!** ✨\n\n"
                "🎬 **SK4FILM Community**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ **Important Rules:**\n"
                "• No links or @mentions\n"
                "• Messages auto-delete after 5 minutes\n\n"
                "👇 **Click colored buttons below** 👇"
            )
            
            try:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=IMAGE_URL,
                    caption=caption,
                    parse_mode="markdown",
                    reply_markup=keyboard
                )
            except:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=caption,
                    parse_mode="markdown",
                    reply_markup=keyboard
                )
                
    except Exception as e:
        logger.error(f"Error welcoming member: {e}")

@app.on_message(filters.text & filters.group)
async def process_message(client, message):
    """Delete links from non-admin messages"""
    try:
        # Ignore bot's own messages
        if message.from_user.is_self or message.from_user.id == client.me.id:
            return
        
        # Check if user is admin
        try:
            chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
            is_admin = chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        except:
            is_admin = False
        
        # Admin messages - NEVER delete
        if is_admin:
            return
        
        # Check for links or mentions
        text = message.text or message.caption or ""
        has_link = bool(re.search(r'http[s]?://|www\.|t\.me/|@', text, re.IGNORECASE))
        
        # If has link/mention, delete immediately
        if has_link:
            try:
                await message.delete()
                logger.info(f"Deleted link from non-admin {message.from_user.id}")
                
                warning = await message.reply_text(
                    "⚠️ **ACCESS DENIED!**\n\nLinks and @mentions are not allowed for non-admin members.\n\n_This message will self-destruct in 10 seconds._",
                    parse_mode="markdown"
                )
                
                asyncio.create_task(
                    delete_message_after_delay(message.chat.id, warning.id, 10)
                )
                return
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
        
        # Schedule regular message deletion
        asyncio.create_task(
            delete_message_after_delay(message.chat.id, message.id, AUTO_DELETE_TIME)
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")

@app.on_callback_query()
async def handle_buttons(client, callback_query: CallbackQuery):
    """Handle colored button clicks"""
    messages = {
        "official_btn": f"🔵 **OFFICIAL CHANNEL**\n\nJoin our official channel for latest updates!\n\n🔗 {OFFICIAL_LINK}",
        "movies_btn": f"🟢 **MOVIES WEBSITE**\n\nVisit our website for exclusive content!\n\n🔗 {MOVIES_LINK}",
        "android_btn": f"🔴 **ANDROID APP**\n\nDownload our app for best experience!\n\n🔗 {ANDROID_LINK}",
        "demo_primary": "✅ You clicked **PRIMARY** (Dark Blue) button!",
        "demo_success": "✅ You clicked **SUCCESS** (Green) button!",
        "demo_danger": "✅ You clicked **DANGER** (Red) button!"
    }
    
    try:
        # Show quick alert
        await callback_query.answer(
            "Opening link... 🔗" if "btn" in callback_query.data else "Button clicked!",
            show_alert=False
        )
        
        # Send the message with link/info
        msg = await callback_query.message.reply_text(
            messages.get(callback_query.data, "Button clicked!"),
            parse_mode="markdown",
            disable_web_page_preview=False
        )
        
        # Auto-delete after 30 seconds
        asyncio.create_task(
            delete_message_after_delay(callback_query.message.chat.id, msg.id, 30)
        )
        
    except Exception as e:
        logger.error(f"Error in callback: {e}")

@app.on_message(filters.command("ping"))
async def ping_command(client, message):
    """Check if bot is alive"""
    await message.reply_text("🏓 Pong! Bot is alive with colored buttons!")

async def main():
    """Main function"""
    logger.info("🎨 SK4FILM Bot Started with Colored Buttons! 🚀")
    logger.info("✅ ButtonStyle.PRIMARY - Dark Blue")
    logger.info("✅ ButtonStyle.SUCCESS - Green")
    logger.info("✅ ButtonStyle.DANGER - Red")
    logger.info("✅ Auto-approve join requests - ACTIVE")
    logger.info("✅ Admin protection - ACTIVE")
    logger.info("✅ Delete links/mentions - ACTIVE")
    logger.info("✅ Auto-delete after 5 minutes - ACTIVE")
    
    print("\n" + "="*60)
    print("🤖 SK4FILM BOT IS RUNNING SUCCESSFULLY!")
    print("="*60)
    print(f"🔵 Official Channel: {OFFICIAL_LINK}")
    print(f"🟢 Movies Website: {MOVIES_LINK}")
    print(f"🔴 Android App: {ANDROID_LINK}")
    print("="*60)
    print("\n📱 Commands available:")
    print("   /start - Start the bot")
    print("   /colors - Demo colored buttons")
    print("   /ping - Check status")
    print("="*60 + "\n")
    
    # Keep bot running
    await client.idle()

if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
