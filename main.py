import logging
import os
import asyncio
import re
from aiohttp import web
from telegram import Update, ChatMemberUpdated, ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ChatMemberHandler,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
)
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("No BOT_TOKEN found in environment variables!")
    exit(1)

class TelegramBot:
    def __init__(self):
        self.application = None
        self.runner = None
        self.site = None
        self.stop_event = asyncio.Event()
        self.AUTO_DELETE_TIME = 300  # 5 minutes in seconds (changed from 120 to 300)
        self.DELETE_LINK_MESSAGE = True
        
        # Image URL for welcome/start message
        self.IMAGE_URL = "https://i.ibb.co/VYB5J028/x.jpg"

    async def delete_message(self, context: ContextTypes.DEFAULT_TYPE):
        """Delete a message after delay"""
        try:
            await context.bot.delete_message(
                chat_id=context.job.chat_id,
                message_id=context.job.data
            )
            logger.info(f"Deleted message {context.job.data}")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    async def auto_approve_join_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Automatically approve chat join requests and send welcome message with image"""
        try:
            join_request: ChatJoinRequest = update.chat_join_request
            user = join_request.from_user
            
            # Approve the join request
            await join_request.approve()
            logger.info(f"Auto-approved join request for user {user.id} ({user.full_name}) in chat {join_request.chat.id}")
            
            # Send welcome message with image and colorful buttons
            try:
                # Create welcome keyboard
                welcome_keyboard = [
                    [
                        InlineKeyboardButton(
                            text="🔵 Official Channel", 
                            url="https://t.me/+0iMDc7jCLThkNmRl"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🟢 Official Website", 
                            url="https://sk4film.vercel.app/"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔴 Android App", 
                            url="https://t.me/How_to_Download_Sk/102"
                        )
                    ]
                ]
                
                reply_markup = InlineKeyboardMarkup(welcome_keyboard)
                
                # Welcome message caption
                caption = (
                    f"✨ *Welcome {user.first_name}!* ✨\n\n"
                    "🎬 *Your Ultimate Entertainment Partner*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "🌟 *Connect with us:*\n"
                    "• 📢 Get latest updates\n"
                    "• 🎯 Access exclusive content\n"
                    "• 📱 Download our Android App\n"
                    "• 💬 Join our community\n\n"
                    "👇 *Click the buttons below to explore!* 👇\n\n"
                    "⚠️ *Group Rules:*\n"
                    "• No links or @mentions allowed\n"
                    "• Your messages will auto-delete after 5 minutes\n"
                    "• Respect all members\n\n"
                    "_Enjoy your stay! 🎉_"
                )
                
                # Send photo with caption and buttons
                await context.bot.send_photo(
                    chat_id=join_request.chat.id,
                    photo=self.IMAGE_URL,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
            except Exception as e:
                logger.error(f"Error sending welcome message with image: {e}")
                # Fallback: send text message if image fails
                try:
                    fallback_msg = await context.bot.send_message(
                        chat_id=join_request.chat.id,
                        text=f"🎉 Welcome {user.mention_html()} to the group!\n\n"
                             f"Official Channel: https://t.me/+0iMDc7jCLThkNmRl\n"
                             f"Website: https://sk4film.vercel.app/\n"
                             f"Android App: https://t.me/How_to_Download_Sk/102",
                        parse_mode='HTML'
                    )
                    context.job_queue.run_once(
                        self.delete_message,
                        60,
                        chat_id=fallback_msg.chat_id,
                        data=fallback_msg.message_id,
                        name=f"del_welcome_{fallback_msg.message_id}"
                    )
                except Exception as e2:
                    logger.error(f"Error sending fallback message: {e2}")
                
        except Exception as e:
            logger.error(f"Error auto-approving join request: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with image and colorful buttons"""
        try:
            # Create colorful buttons
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="🔵 📢 Official Channel", 
                        url="https://t.me/+0iMDc7jCLThkNmRl"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🟢 🌐 Official Website", 
                        url="https://sk4film.vercel.app/"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔴 📱 Android App", 
                        url="https://t.me/How_to_Download_Sk/102"
                    )
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Caption text with formatting
            caption = (
                "✨ *Welcome to SK4Film Bot!* ✨\n\n"
                "🎬 *Your Ultimate Entertainment Partner*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🌟 *What we offer:*\n"
                "• 📢 Latest movie updates\n"
                "• 🎯 Exclusive content\n"
                "• 📱 Android App access\n"
                "• 💬 24/7 support\n\n"
                "🌟 *Connect with us:*\n"
                "• Click buttons below to join\n"
                "• Get instant updates\n"
                "• Never miss any content\n\n"
                "👇 *Click the buttons below to explore!* 👇\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "_Thank you for choosing SK4Film!_ 🎉"
            )
            
            # Send photo with caption and buttons
            try:
                await update.message.reply_photo(
                    photo=self.IMAGE_URL,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                # Fallback: send text message only
                await update.message.reply_text(
                    caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            
            # Delete the /start command message (optional)
            try:
                await update.message.delete()
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            # Super fallback
            try:
                await update.message.reply_text(
                    "🤖 *SK4Film Bot*\n\n"
                    "• Official Channel: https://t.me/+0iMDc7jCLThkNmRl\n"
                    "• Official Website: https://sk4film.vercel.app/\n"
                    "• Android App: https://t.me/How_to_Download_Sk/102",
                    parse_mode='Markdown'
                )
            except:
                pass

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()  # Acknowledge button press
        
        # Send info messages based on button clicked
        if query.data == "channel":
            msg = await query.message.reply_text(
                "📢 **Official Telegram Channel**\n\n"
                "Join our channel for:\n"
                "• Daily updates\n"
                "• Latest news\n"
                "• Exclusive content\n"
                "• Community posts\n\n"
                "[Click here to join](https://t.me/+0iMDc7jCLThkNmRl)",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            # Auto-delete info message after 30 seconds
            context.job_queue.run_once(
                self.delete_message,
                30,
                chat_id=msg.chat_id,
                data=msg.message_id,
                name=f"del_info_{msg.message_id}"
            )
        elif query.data == "website":
            msg = await query.message.reply_text(
                "🌐 **Official Website**\n\n"
                "Visit our website for:\n"
                "• Movies & Shows\n"
                "• Latest updates\n"
                "• Download links\n"
                "• Support & Help\n\n"
                "[SK4Film Website](https://sk4film.vercel.app/)",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            context.job_queue.run_once(
                self.delete_message,
                30,
                chat_id=msg.chat_id,
                data=msg.message_id,
                name=f"del_info_{msg.message_id}"
            )
        elif query.data == "app":
            msg = await query.message.reply_text(
                "📱 **Official Android App**\n\n"
                "Download our app for:\n"
                "• Better experience\n"
                "• Faster streaming\n"
                "• Offline downloads\n"
                "• Exclusive features\n\n"
                "[Download Now](https://t.me/How_to_Download_Sk/102)",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            context.job_queue.run_once(
                self.delete_message,
                30,
                chat_id=msg.chat_id,
                data=msg.message_id,
                name=f"del_info_{msg.message_id}"
            )

    async def is_admin(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
        """Check if a user is an admin in the chat"""
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            admin_ids = [admin.user.id for admin in admins]
            return user_id in admin_ids
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False

    async def has_link_or_mention(self, text: str) -> bool:
        """Check if message contains link or username mention"""
        patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
            r'www\.[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+(?:/[^\s]*)?',  # www URLs
            r't\.me/[a-zA-Z0-9_]+',  # Telegram links
            r'@[a-zA-Z0-9_]+',  # Username mentions
            r'🔗',  # Link emoji
            r'⚡️',  # Spam emoji
            r'📱',  # App emoji
            r'🎬',  # Movie emoji
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process all messages - delete links/mentions from non-admins"""
        try:
            message = update.message
            if not message or not message.text:
                return

            # Check if user is admin
            is_user_admin = await self.is_admin(context, message.chat.id, message.from_user.id)
            
            # IMPORTANT: Administrators' messages are NEVER deleted
            if is_user_admin:
                logger.debug(f"Admin {message.from_user.id} message - not deleting")
                return

            logger.debug(f"Processing non-admin message from {message.from_user.id}")
            
            # Check for links/usernames in message
            if self.DELETE_LINK_MESSAGE and await self.has_link_or_mention(message.text):
                try:
                    # Delete the message immediately
                    await message.delete()
                    logger.info(f"Deleted message with link/username from non-admin {message.from_user.id}")
                    
                    # Send warning message
                    warning = await context.bot.send_message(
                        chat_id=message.chat.id,
                        text="⚠️ **Warning!**\n\nLinks, @mentions, and promotional content are not allowed for non-admin members!\n\n_This message will auto-delete in 10 seconds._",
                        parse_mode='Markdown',
                        reply_to_message_id=message.message_id
                    )
                    # Schedule warning deletion after 10 seconds
                    context.job_queue.run_once(
                        self.delete_message,
                        10,
                        chat_id=warning.chat_id,
                        data=warning.message_id,
                        name=f"del_warn_{warning.message_id}"
                    )
                    return
                except Exception as e:
                    logger.error(f"Error deleting link message: {e}")
            
            # Schedule regular message deletion (5 minutes for non-admins)
            context.job_queue.run_once(
                self.delete_message,
                self.AUTO_DELETE_TIME,  # 5 minutes
                chat_id=message.chat_id,
                data=message.message_id,
                name=f"del_msg_{message.message_id}"
            )
            logger.debug(f"Scheduled deletion for message {message.message_id} in {self.AUTO_DELETE_TIME}s")
                
        except Exception as e:
            logger.error(f"Message processing error: {e}", exc_info=True)

    async def track_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Track when new members join via invite links"""
        try:
            chat_member_update: ChatMemberUpdated = update.chat_member
            old_status = chat_member_update.old_chat_member.status
            new_status = chat_member_update.new_chat_member.status
            user = chat_member_update.new_chat_member.user
            
            # Check if user joined (not an admin)
            if (old_status in ['left', 'kicked'] and new_status == 'member') or new_status == 'member':
                if not await self.is_admin(context, chat_member_update.chat.id, user.id):
                    logger.info(f"User {user.id} ({user.full_name}) joined the chat via invite link")
                    
                    # Send welcome message with image for invite link joins
                    try:
                        welcome_keyboard = [
                            [InlineKeyboardButton("🔵 Join Channel", url="https://t.me/+0iMDc7jCLThkNmRl")],
                            [InlineKeyboardButton("🟢 Visit Website", url="https://sk4film.vercel.app/")],
                            [InlineKeyboardButton("🔴 Download App", url="https://t.me/How_to_Download_Sk/102")]
                        ]
                        reply_markup = InlineKeyboardMarkup(welcome_keyboard)
                        
                        caption = (
                            f"✨ *Welcome {user.first_name}!* ✨\n\n"
                            "🎬 **Welcome to SK4Film Community!**\n\n"
                            "⚠️ *Important Rules:*\n"
                            "• ❌ No links or @mentions\n"
                            "• ⏰ Messages auto-delete after 5 minutes\n"
                            "• 👑 Admins are exempt from rules\n\n"
                            "👇 *Connect with us:*"
                        )
                        
                        await context.bot.send_photo(
                            chat_id=chat_member_update.chat.id,
                            photo=self.IMAGE_URL,
                            caption=caption,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                    except Exception as e:
                        logger.error(f"Error sending welcome image: {e}")
                        # Fallback text message
                        warning_msg = await context.bot.send_message(
                            chat_id=chat_member_update.chat.id,
                            text=f"👋 Welcome {user.first_name}!\n\n"
                                 f"⚠️ **Group Rules:**\n"
                                 f"• Messages with links or @mentions will be automatically deleted\n"
                                 f"• All non-admin messages will be deleted after 5 minutes\n\n"
                                 f"📢 Channel: https://t.me/+0iMDc7jCLThkNmRl\n"
                                 f"🌐 Website: https://sk4film.vercel.app/\n"
                                 f"📱 App: https://t.me/How_to_Download_Sk/102",
                            parse_mode='Markdown'
                        )
                        context.job_queue.run_once(
                            self.delete_message,
                            120,
                            chat_id=warning_msg.chat_id,
                            data=warning_msg.message_id,
                            name=f"del_welcome_warning_{warning_msg.message_id}"
                        )
                        
        except Exception as e:
            logger.error(f"Error tracking chat members: {e}")

    async def health_check(self, request):
        """Health check endpoint"""
        return web.Response(text="Bot is running")

    async def start_web_server(self):
        """Start health check web server"""
        try:
            app = web.Application()
            app.router.add_get("/", self.health_check)
            app.router.add_get("/health", self.health_check)
            self.runner = web.AppRunner(app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, "0.0.0.0", int(os.getenv("PORT", "8000")))
            await self.site.start()
            logger.info("Health check server running")
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")

    async def initialize_bot(self):
        """Initialize bot with all handlers"""
        try:
            self.application = (
                Application.builder()
                .token(BOT_TOKEN)
                .concurrent_updates(True)
                .build()
            )

            # Add all handlers
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            self.application.add_handler(ChatJoinRequestHandler(self.auto_approve_join_request))
            self.application.add_handler(ChatMemberHandler(self.track_chat_members, ChatMemberHandler.CHAT_MEMBER))
            
            # Message handler for non-admin messages
            message_filter = filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE
            self.application.add_handler(MessageHandler(message_filter, self.process_message))
            
            await self.application.initialize()
            await self.application.start()
            logger.info("Bot initialized successfully")
            logger.info(f"Features enabled: Auto-approve joins, Delete non-admin links, Auto-delete after {self.AUTO_DELETE_TIME}s")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise

    async def run_bot(self):
        """Run bot with polling"""
        try:
            logger.info("Starting bot polling...")
            await self.application.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot is now running with auto-approval and message management")
            await self.stop_event.wait()
        except asyncio.CancelledError:
            logger.info("Bot shutdown requested")
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Shutdown bot gracefully"""
        logger.info("Shutting down bot...")
        try:
            if self.application:
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")

        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
        except Exception as e:
            logger.error(f"Error during web server shutdown: {e}")

        logger.info("Shutdown complete")

    async def run(self):
        """Main run method"""
        try:
            await self.start_web_server()
            await self.initialize_bot()
            await self.run_bot()
        except Exception as e:
            logger.error(f"Fatal error in bot: {e}", exc_info=True)
        finally:
            self.stop_event.set()
            await self.shutdown()

async def main():
    """Main entry point"""
    logger.info("Starting SK4Film Bot...")
    bot = TelegramBot()
    try:
        await bot.run()
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
    finally:
        logger.info("Application shutdown complete")
