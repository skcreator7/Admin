from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import ChatMember
import logging
import time

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Your bot token (replace 'YOUR_TOKEN' with your actual bot token)
TOKEN = 'YOUR_TOKEN'


# Start command - to welcome new users and show bot information
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Hello! I am your group management bot. I can help you manage your group by performing various tasks.\n"
        "Here are some commands you can use:\n"
        "/setwelcome <message> - Set a welcome message\n"
        "/showwelcome - Show the current welcome message"
    )


# Set welcome message
def set_welcome(update: Update, context: CallbackContext) -> None:
    if context.args:
        welcome_message = ' '.join(context.args)
        context.chat_data['welcome_message'] = welcome_message
        update.message.reply_text(f"Welcome message set to: {welcome_message}")
    else:
        update.message.reply_text("Please provide a welcome message after the command.\nExample: /setwelcome Hello, welcome to the group!")


# Show current welcome message
def show_welcome(update: Update, context: CallbackContext) -> None:
    welcome_message = context.chat_data.get('welcome_message', None)
    if welcome_message:
        update.message.reply_text(f"Current welcome message: {welcome_message}")
    else:
        update.message.reply_text("No welcome message set yet.")


# Handle new users joining the group
def welcome_new_member(update: Update, context: CallbackContext) -> None:
    new_user = update.message.new_chat_members[0]
    welcome_message = context.chat_data.get('welcome_message', "Welcome to the group!")
    update.message.reply_text(f"{welcome_message} {new_user.first_name}!")


# Delete messages containing links or usernames (@)
def delete_links_and_usernames(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text

    # Check if the message contains a link or @username
    if "http" in message_text or "@" in message_text:
        # Delete the message
        update.message.delete()

        # Send a warning message to the user
        update.message.reply_text(
            "Links and usernames (@) are not allowed here. Please refrain from sending such messages."
        )


# Function to automatically delete user messages after 5 minutes
def auto_delete_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # Get the message's timestamp (this is in seconds)
    timestamp = time.time()

    # Delay of 5 minutes (300 seconds)
    context.job_queue.run_once(delete_message, 300, context=(chat_id, update.message.message_id))


# Delete the message after 5 minutes
def delete_message(context: CallbackContext) -> None:
    chat_id, message_id = context.job.context
    try:
        context.bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")


# Function to determine if the user is an admin
def is_admin(update: Update) -> bool:
    user = update.message.from_user
    chat_id = update.message.chat_id

    # Get the chat member status (whether the user is an admin)
    member = update.bot.get_chat_member(chat_id, user.id)
    return member.status in [ChatMember.ADMINISTRATOR, ChatMember.CREATOR]


# Message handler to delete non-admin user messages after 5 minutes
def handle_user_message(update: Update, context: CallbackContext) -> None:
    if not is_admin(update):  # Only auto-delete non-admin messages
        auto_delete_message(update, context)


# Main function to set up the bot
def main():
    # Create an Updater object and attach the dispatcher
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Command Handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('setwelcome', set_welcome))
    dispatcher.add_handler(CommandHandler('showwelcome', show_welcome))

    # Message Handler to welcome new members
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_new_member))

    # Message Handler to delete messages containing links or usernames
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, delete_links_and_usernames))

    # Message Handler for general user messages (auto delete after 5 minutes)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_user_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop it
    updater.idle()


# Run the bot
if __name__ == '__main__':
    main()
