import os
import logging
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Example start command
def start(update, context):
    update.message.reply_text("Hello! Your trading bot is running.")

# Example help command
def help_command(update, context):
    update.message.reply_text("Use /start to test the bot. More commands coming soon.")

# Example echo handler
def echo(update, context):
    update.message.reply_text(update.message.text)

def main():
    # Get token from environment variable
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN not set in environment variables")
        return

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    # Register handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
