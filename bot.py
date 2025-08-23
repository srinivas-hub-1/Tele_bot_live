import os
import logging
from flask import Flask, request
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
flask_app = Flask(__name__)

# Get environment variables
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
API_KEY = os.environ.get('GEMINI_API_KEY')

# Configure Gemini
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    logger.warning("GEMINI_API_KEY not set")

def generate_content(prompt: str) -> str:
    try:
        if not API_KEY:
            return "Error: Gemini API key not configured."
        
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else "Sorry, I couldn't generate a response."
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return f"Error: {str(e)}"

@flask_app.route('/')
def home():
    return "🤖 Telegram Bot with Gemini AI is running! Use webhook for Telegram."

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Simple webhook handler that just acknowledges receipt"""
    if request.method == "POST":
        # For now, just acknowledge receipt
        # In a real implementation, you'd process the Telegram update here
        data = request.get_json()
        logger.info(f"Received webhook: {data}")
        return "OK"
    return "Method not allowed", 405

# For local testing with polling
if __name__ == '__main__':
    if not os.environ.get('RENDER'):
        # Local development with polling
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
        
        def start(update, context):
            update.message.reply_text("🤖 Hello! I'M Nivas AI bot. Send me a message!")
        
        def help_cmd(update, context):
            update.message.reply_text("Just send me any text message and I'll respond")
        
        def echo(update, context):
            user_text = update.message.text
            response = generate_content(user_text)
            update.message.reply_text(response)
        
        if TOKEN:
            updater = Updater(TOKEN, use_context=True)
            dp = updater.dispatcher
            dp.add_handler(CommandHandler("start", start))
            dp.add_handler(CommandHandler("help", help_cmd))
            dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
            
            updater.start_polling()
            updater.idle()
        else:
            logger.error("TELEGRAM_BOT_TOKEN not set for local polling")
    else:
        # On Render, just run the Flask app
        flask_app.run(host='0.0.0.0', port=5000)
