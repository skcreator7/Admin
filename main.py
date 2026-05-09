import asyncio
import re
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
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
OFFICIAL_LINK = "https://t.me/+0iMDc7jCLThkNmRl"
MOVIES_LINK = "https://sk4film.vercel.app/"
ANDROID_LINK = "https://t.me/How_to_Download_Sk/102"
AUTO_DELETE_TIME = 300

# Initialize Pyrogram Client
app = Client("sk4film_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def delete_message_after_delay(chat_id, message_id, delay):
    """Delete message after delay"""
    try:
        await asyncio.sleep(delay)
        await app.delete_messages(chat_id, message_id)
        logger.info(f"Deleted message {message_id}")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

def get_colored_keyboard():
    """Create colored keyboard with emojis (visual colors)"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="🔵 OFFICIAL CHANNEL",
                callback_data="official_btn"
            )
        ],
        [
            InlineKeyboardButton(
                text="🟢 MOVIES WEBSITE",
                callback_data="movies_btn"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔴 ANDROID APP",
                callback_data="android_btn"
            )
        ]
    ])

@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Handle /start command"""
    try:
        await message.delete()
        
        keyboard = get_colored_keyboard()
        
        caption = (
            "✨ **WELCOME TO SK4FILM BOT** ✨\n\n"
            "🎬 **Your Ultimate Entertainment Partner**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🌟 **Choose an option below:**\n\n"
            "🔵 **Official Channel** - Get latest updates\n"
            "🟢 **Movies Website** - Browse exclusive content\n"
            "🔴 **Android App** - Download & install\n\n"
            "👇 **Click buttons below** 👇\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "_Thank you for choosing SK4Film!_ 🎉"
        )
        
        try:
            msg = await message.reply_photo(
                photo=IMAGE_URL,
                caption=caption,
                parse_mode="markdown",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending image: {e}")
            msg = await message.reply_text(
                caption,
                parse_mode="markdown",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        
        asyncio.create_task(
            delete_message_after_delay(message.chat.id, msg.id, AUTO_DELETE_TIME)
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@app.on_message(filters.command("help"))
async def help_command(client, message):
    """Help command"""
    help_text = (
        "📚 **SK4FILM Bot Commands**\n\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/ping - Check bot status\n"
        "/rules - Show group rules\n\n"
        "**Features:**\n"
        "✅ Auto-approve join requests\n"
        "✅ Delete links from non-admins\n"
        "✅ Auto-delete messages after 5 minutes\n"
        "✅ Welcome new members"
    )
    await message.reply_text(help_text, parse_mode="markdown")

@app.on_message(filters.command("ping"))
async def ping_command(client, message):
    """Ping command"""
    await message.reply_text("🏓 Pong! Bot is alive!")

@app.on_message(filters.command("rules"))
async def rules_command(client, message):
    """Show rules"""
    rules = (
        "📜 **SK4FILM Group Rules**\n\n"
        "1️⃣ No links or @mentions allowed\n"
        "2️⃣ No spam or promotional content\n"
        "3️⃣ Respect all members\n"
        "4️⃣ Admins' decisions are final\n"
        "5️⃣ Non-admin messages auto-delete after 5 minutes"
    )
    await message.reply_text(rules, parse_mode="markdown")

@app.on_chat_join_request()
async def auto_approve_join_request(client, join_request):
    """Auto approve join requests"""
    try:
        await join_request.approve()
        logger.info(f"Auto-approved join request from {join_request.from_user.id}")
        
        keyboard = get_colored_keyboard()
        
        caption = (
            f"✨ **Welcome {join_request.from_user.first_name}!** ✨\n\n"
            "🎬 **SK4FILM Community**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ **Group Rules:**\n"
            "• ❌ No links or @mentions\n"
            "• ⏰ Messages auto-delete after 5 minutes\n"
            "• 👑 Admins are exempt\n\n"
            "👇 **Click buttons below** 👇"
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
    """Welcome new members"""
    try:
        for new_member in message.new_chat_members:
            if new_member.id == client.me.id:
                continue
            
            try:
                chat_member = await client.get_chat_member(message.chat.id, new_member.id)
                if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    continue
            except:
                pass
            
            keyboard = get_colored_keyboard()
            
            caption = (
                f"✨ **Welcome {new_member.first_name}!** ✨\n\n"
                "🎬 **SK4FILM Community**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ **Important Rules:**\n"
                "• No links or @mentions\n"
                "• Messages auto-delete after 5 minutes\n\n"
                "👇 **Click buttons below** 👇"
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
    """Process messages - delete links from non-admins"""
    try:
        if message.from_user.is_self or message.from_user.id == client.me.id:
            return
        
        try:
            chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
            is_admin = chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        except:
            is_admin = False
        
        if is_admin:
            return
        
        text = message.text or message.caption or ""
        has_link = bool(re.search(r'http[s]?://|www\.|t\.me/|@', text, re.IGNORECASE))
        
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
        
        asyncio.create_task(
            delete_message_after_delay(message.chat.id, message.id, AUTO_DELETE_TIME)
        )
        
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Error processing message: {e}")

@app.on_callback_query()
async def handle_buttons(client, callback_query: CallbackQuery):
    """Handle button clicks"""
    messages = {
        "official_btn": f"🔵 **OFFICIAL CHANNEL**\n\n🔗 {OFFICIAL_LINK}",
        "movies_btn": f"🟢 **MOVIES WEBSITE**\n\n🔗 {MOVIES_LINK}",
        "android_btn": f"🔴 **ANDROID APP**\n\n🔗 {ANDROID_LINK}"
    }
    
    try:
        await callback_query.answer("Opening...", show_alert=False)
        
        msg = await callback_query.message.reply_text(
            messages.get(callback_query.data, "Button clicked!"),
            parse_mode="markdown",
            disable_web_page_preview=False
        )
        
        asyncio.create_task(
            delete_message_after_delay(callback_query.message.chat.id, msg.id, 30)
        )
        
    except Exception as e:
        logger.error(f"Error in callback: {e}")

async def main():
    """Main function"""
    print("\n" + "="*60)
    print("🤖 SK4FILM BOT IS RUNNING SUCCESSFULLY!")
    print("="*60)
    print(f"🔵 Official Channel: {OFFICIAL_LINK}")
    print(f"🟢 Movies Website: {MOVIES_LINK}")
    print(f"🔴 Android App: {ANDROID_LINK}")
    print("="*60)
    print("\nCommands: /start, /help, /ping, /rules")
    print("="*60 + "\n")
    
    logger.info("🎨 SK4FILM Bot Started!")
    logger.info("✅ Auto-approve join requests - ACTIVE")
    logger.info("✅ Admin protection - ACTIVE")
    logger.info("✅ Delete links/mentions - ACTIVE")
    logger.info("✅ Auto-delete after 5 minutes - ACTIVE")
    
    await client.idle()

if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Error: {e}")
