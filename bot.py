import os
import logging
import requests
from flask import Flask, request
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
flask_app = Flask(__name__)

# Get environment variables
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
API_KEY = os.environ.get('GEMINI_API_KEY')

# Configure Gemini
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini AI configured successfully")
else:
    logger.warning("GEMINI_API_KEY not set")

def generate_content(prompt: str) -> str:
    """Generate response using Gemini AI."""
    try:
        if not API_KEY:
            return "❌ Error: Gemini API key not configured. Please check your environment variables."
        
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else "Sorry, I couldn't generate a response."
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return f"⚠️ Error: {str(e)}"

def send_telegram_message(chat_id, text):
    """Send a message to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text
        }
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return None

@flask_app.route('/')
def home():
    return "🤖 Nivas AI! Send a message to your bot."

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming updates from Telegram and send responses."""
    if request.method == "POST":
        try:
            data = request.get_json()
            logger.info(f"Received webhook: {data}")
            
            # Check if it's a message with text
            if 'message' in data and 'text' in data['message']:
                chat_id = data['message']['chat']['id']
                text = data['message']['text']
                
                logger.info(f"Processing message from {chat_id}: {text}")
                
                # Handle commands
                if text.startswith('/'):
                    if text == '/start':
                        response_text = """
🤖 Hello! I'm Nivas AI

Send me any text message and I'll generate a response.

• Ask me question
• Get ideas and suggestions
• Have a conversation!

Just type your message and I'll help you!
                        """
                    elif text == '/help':
                        response_text = """
ℹ️ How to use this bot:

• Just send me any text message
• I'll respond
• You can ask questions, get ideas, or just chat!
*Admin : Message @Learnforrfreee — I'll reply there*

*Commands:*
/start - Start the bot
/help - Show this help message
                        """
                    else:
                        response_text = "❌ Sorry, I don't understand that command. Try /help for instructions."
                
                else:
                    # Generate response using Gemini for regular messages
                    response_text = generate_content(text)
                
                # Send response back to Telegram
                send_telegram_message(chat_id, response_text)
                logger.info(f"Sent response to {chat_id}")
            
            return "OK"
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return "Error", 500
    
    return "Method not allowed", 405

# For local testing with polling
if __name__ == '__main__':
    if not os.environ.get('RENDER'):
        # Local development with polling
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
        
        def start(update, context):
            update.message.reply_text("🤖 Hello! I'm your Gemini AI bot. Send me a message!")
        
        def help_cmd(update, context):
            update.message.reply_text("Just send me any text message and I'll respond with Gemini AI!")
        
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
            logger.info("Bot is polling locally...")
            updater.idle()
        else:
            logger.error("TELEGRAM_BOT_TOKEN not set for local polling")
    else:
        # On Render, just run the Flask app
        flask_app.run(host='0.0.0.0', port=5000)

