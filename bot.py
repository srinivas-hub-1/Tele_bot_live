from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import google.generativeai as genai
import os
import logging
from flask import Flask, request
import threading
import asyncio

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token and API Key - Will be set as environment variables
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
API_KEY = os.environ.get('GEMINI_API_KEY')

# Configure Gemini model
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")

def generate_content(prompt: str) -> str:
    try:
        if not API_KEY:
            return "Error: Gemini API key not configured. Please check your environment variables."
        
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else "Sorry, I couldn't generate a response."
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return f"Error: {str(e)}"

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    welcome_text = """
🤖 Hello! I'm your Gemini AI Assistant.

Send me any text message and I'll generate a response using Google's Gemini AI.

Just type your message and I'll help you!
    """
    update.message.reply_text(welcome_text)

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a help message when the command /help is issued."""
    help_text = """
ℹ️ How to use this bot:

• Just send me any text message
• I'll respond using Gemini AI
• You can ask questions, get ideas, or just chat!

Commands:
/start - Start the bot
/help - Show this help message
    """
    update.message.reply_text(help_text)

def chat(update: Update, context: CallbackContext) -> None:
    """Handle incoming text messages."""
    user_message = update.message.text
    
    # Don't process empty messages
    if not user_message.strip():
        update.message.reply_text("Please send a text message to chat!")
        return
    
    thinking_msg = update.message.reply_text("🤔 Thinking...")
    
    try:
        response_text = generate_content(user_message)
        
        # Delete the thinking message
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=thinking_msg.message_id)
        
        # Send the response (split if too long for Telegram)
        if len(response_text) > 4096:
            for i in range(0, len(response_text), 4096):
                update.message.reply_text(response_text[i:i+4096])
        else:
            update.message.reply_text(response_text)
            
    except Exception as e:
        logger.error(f"Error in chat handler: {str(e)}")
        update.message.reply_text("Sorry, I encountered an error. Please try again later.")

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")

# Initialize Flask app
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "🤖 Telegram Bot with Gemini AI is running!"

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming updates from Telegram."""
    if request.method == "POST":
        update = Update.de_json(request.get_json(), bot)
        dispatcher.process_update(update)
    return "OK"

# Create bot instance
def create_bot():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return None
    
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, chat))
    dispatcher.add_error_handler(error_handler)
    
    return updater

# Global variables for webhook mode
updater = None
dispatcher = None
bot = None

if __name__ == '__main__':
    # For webhook deployment
    updater = create_bot()
    if updater:
        bot = updater.bot
        dispatcher = updater.dispatcher
        # Flask app will be run by gunicorn
