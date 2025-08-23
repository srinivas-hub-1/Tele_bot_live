from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import asyncio
import os
import logging

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
    model = genai.GenerativeModel('gemini-1.5-flash')
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    welcome_text = """
🤖 Hello! I'm your Gemini AI Assistant.

Send me any text message and I'll generate a response using Google's Gemini AI.

Features:
• AI-powered responses
• Fast and reliable
• Always learning

Just type your message and I'll help you!
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    help_text = """
ℹ️ How to use this bot:

• Just send me any text message
• I'll respond using Gemini AI
• You can ask questions, get ideas, or just chat!

Commands:
/start - Start the bot
/help - Show this help message

No voice messages - text only!
    """
    await update.message.reply_text(help_text)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    user_message = update.message.text
    
    # Don't process empty messages
    if not user_message.strip():
        await update.message.reply_text("Please send a text message to chat!")
        return
    
    # Show typing action
    async with update.message.chat.action(action='typing'):
        # Send thinking message
        thinking_msg = await update.message.reply_text("🤔 Thinking...")
        
        try:
            # Run the blocking Gemini call in a thread pool
            response_text = await asyncio.get_event_loop().run_in_executor(
                None, generate_content, user_message
            )
            
            # Delete the thinking message
            await thinking_msg.delete()
            
            # Send the response (split if too long for Telegram)
            if len(response_text) > 4096:
                for i in range(0, len(response_text), 4096):
                    await update.message.reply_text(response_text[i:i+4096])
            else:
                await update.message.reply_text(response_text)
                
        except Exception as e:
            logger.error(f"Error in chat handler: {str(e)}")
            await thinking_msg.delete()
            await update.message.reply_text("Sorry, I encountered an error. Please try again later.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")

# Build the bot application
def create_application():
    """Create and configure the Telegram bot application."""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        raise ValueError("Telegram bot token is required")
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    return application

# Create the application instance
app = create_application()