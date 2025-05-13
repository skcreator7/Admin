import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
from time import time

# Load environment variables from .env file
load_dotenv()

# Get the BOT_TOKEN from the environment variables
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Command to start the bot
async def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the /start command is used."""
    await update.message.reply_text("Hello! I am your group management bot.")

# Function to handle new member joins
async def welcome(update: Update, context: CallbackContext) -> None:
    """Welcome new members to the group."""
    new_members = update.message.new_chat_members
    for member in new_members:
        await update.message.reply_text(f"Welcome {member.full_name} to the group!")

# Function to delete messages with links or @usernames
async def delete_unwanted_messages(update: Update, context: CallbackContext) -> None:
    """Delete messages containing links or @usernames."""
    message = update.message
    if 'http' in message.text or '@' in message.text:
        await message.delete()
        await update.message.reply_text("Links and @usernames are not allowed!")

# Function to automatically delete messages after 5 minutes
async def auto_delete_message(update: Update, context: CallbackContext) -> None:
    """Schedule a message to be deleted after 5 minutes."""
    context.job_queue.run_once(delete_message, 300, context=update.message)

async def delete_message(context: CallbackContext) -> None:
    """Delete a message."""
    await context.job.context.delete()

# Handler for unknown commands
async def unknown(update: Update, context: CallbackContext) -> None:
    """Handle unknown commands."""
    await update.message.reply_text("Sorry, I didn't understand that command.")

# Main function to start the bot
def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    
    # Register message handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_unwanted_messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_delete_message))

    # Register unknown command handler
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
