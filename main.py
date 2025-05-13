import logging
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
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
def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the /start command is used."""
    update.message.reply_text("Hello! I am your group management bot.")

# Function to handle new member joins
def welcome(update: Update, context: CallbackContext) -> None:
    """Welcome new members to the group."""
    new_members = update.message.new_chat_members
    for member in new_members:
        update.message.reply_text(f"Welcome {member.full_name} to the group!")

# Function to delete messages with links or @usernames
def delete_unwanted_messages(update: Update, context: CallbackContext) -> None:
    """Delete messages containing links or @usernames."""
    message = update.message
    if 'http' in message.text or '@' in message.text:
        message.delete()
        update.message.reply_text("Links and @usernames are not allowed!")

# Function to automatically delete messages after 5 minutes
def auto_delete_message(update: Update, context: CallbackContext) -> None:
    """Schedule a message to be deleted after 5 minutes."""
    context.job_queue.run_once(delete_message, 300, context=update.message)

def delete_message(context: CallbackContext) -> None:
    """Delete a message."""
    context.job.context.delete()

# Handler for unknown commands
def unknown(update: Update, context: CallbackContext) -> None:
    """Handle unknown commands."""
    update.message.reply_text("Sorry, I didn't understand that command.")

# Main function to start the bot
def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    
    # Register message handlers
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, delete_unwanted_messages))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, auto_delete_message))

    # Register unknown command handler
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop
    updater.idle()

if __name__ == '__main__':
    main()
