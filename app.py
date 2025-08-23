from flask import Flask, request
from bot import app as telegram_app
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    """Home route to check if the bot is running."""
    return "🤖 Telegram Bot with Gemini AI is running! Send a message to your bot to start chatting."

@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle incoming updates from Telegram."""
    if request.method == "POST":
        try:
            # Process the update
            update_data = request.get_json()
            update = await telegram_app.update_queue.get()
            await telegram_app.process_update(update)
            return "OK"
        except Exception as e:
            logger.error(f"Error in webhook: {str(e)}")
            return "Error", 500
    return "Method not allowed", 405

async def set_webhook():
    """Set the webhook for Telegram bot."""
    try:
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')}/webhook"
        await telegram_app.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {str(e)}")

# Initialize the bot when the app starts
@flask_app.before_first_request
async def initialize_bot():
    """Initialize the bot when the Flask app starts."""
    try:
        await telegram_app.initialize()
        await telegram_app.start()
        await set_webhook()
        logger.info("Bot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize bot: {str(e)}")

if __name__ == '__main__':
    # For local development without webhook
    if os.environ.get('RENDER'):
        # On Render, use the Flask app with gunicorn
        flask_app.run(host='0.0.0.0', port=5000)
    else:
        # Local development - use polling
        import asyncio
        async def run_polling():
            await telegram_app.initialize()
            await telegram_app.start()
            await telegram_app.updater.start_polling()
            logger.info("Bot is polling for messages...")
            # Keep the bot running
            await asyncio.Future()
        
        asyncio.run(run_polling())