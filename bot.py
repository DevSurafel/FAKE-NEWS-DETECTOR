import os
import logging
import re
import asyncio
import requests
from typing import Dict, List
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from translate import Translator
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_TOKEN_AI_MODEL = os.getenv("HF_AI_MODEL_API_TOKEN")
API_URL_AI_MODEL = os.getenv("HF_AI_MODEL_API_URL")

# AI model API headers
headers_ai = {"Authorization": f"Bearer {API_TOKEN_AI_MODEL}"}

# Store conversation history for each user
user_conversation_history: Dict[int, List[str]] = {}

# HTML entity character fix
def fix_html_entities(text: str) -> str:
    """Fix HTML entities in translated text."""
    return text.replace("&#39;", "'").replace("&quot;", '"').replace("&amp;", "&")

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using the translate library with error handling."""
    try:
        translator = Translator(from_lang=source_lang, to_lang=target_lang)
        translation = translator.translate(text)
        
        # Fix HTML entities that might appear in translations
        translation = fix_html_entities(translation)
        
        logger.info(f"Successfully translated from {source_lang} to {target_lang}: {translation}")
        return translation
    except Exception as e:
        logger.error(f"Translation error from {source_lang} to {target_lang}: {e}")
        if source_lang == "om" and target_lang == "en":
            return text  # Return original text if translation fails
        elif source_lang == "en" and target_lang == "om":
            return "Dhiifama, rakkina translation qaba. Yeroo muraasa booda irra deebi'aa yaali."
        return text

async def get_ai_response(user_id: int, text: str, max_retries: int = 3, retry_delay: int = 2) -> str:
    """Get AI response with retry logic and conversation history."""
    retries = 0
    
    # Create conversation context from history
    context = ""
    if user_id in user_conversation_history and user_conversation_history[user_id]:
        # Use last 3 conversation turns for context
        context = "\n".join(user_conversation_history[user_id][-3:]) + "\n"
    
    while retries < max_retries:
        try:
            # Include conversation history in prompt
            prompt = f"{context}User: {text}\nAssistant:"
            
            response = requests.post(
                API_URL_AI_MODEL, 
                headers=headers_ai, 
                json={"inputs": prompt},
                timeout=30  # Add timeout to prevent hanging
            )
            response.raise_for_status()
            
            ai_response = response.json()[0]['generated_text']
            
            # Extract just the assistant's response
            ai_response = ai_response.split("Assistant:")[-1].strip()
            ai_response = re.sub(r"User:.*", "", ai_response).strip()
            
            # Update conversation history
            if user_id in user_conversation_history:
                user_conversation_history[user_id].append(f"User: {text}\nAssistant: {ai_response}")
            else:
                user_conversation_history[user_id] = [f"User: {text}\nAssistant: {ai_response}"]
            
            # Keep only the last 5 conversation turns
            user_conversation_history[user_id] = user_conversation_history[user_id][-5:]
            
            logger.info(f"AI Response (English): {ai_response}")
            return ai_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Model API error (retry {retries + 1}/{max_retries}): {e}")
            retries += 1
            if retries < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                return "Maaloo, amma kana yaada keessan qabachuuf rakkina qaba. Yeroo muraasa booda irra deebi'aa yaali."

class AIChatBot:
    def __init__(self, token: str):
        self.token = token
        self.inappropriate_content_pattern = re.compile(
            r"(sexy|porn|nude|sex|xxx|adult|nsfw)", 
            re.IGNORECASE
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        user = update.message.from_user
        user_text = update.message.text
        user_id = user.id
        
        # Check for inappropriate content
        if self.inappropriate_content_pattern.search(user_text):
            await update.message.reply_text("Gaaffii wanta tola hin oolleef deebii hin kennu.")
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
        
        try:
            # Log and translate user input
            logger.info(f"User Input (Oromo): {user_text}")
            translated_input = await translate_text(user_text, source_lang="om", target_lang="en")
            logger.info(f"Translated Input (Oromo to English): {translated_input}")
            
            # Get AI response
            ai_response = await get_ai_response(user_id, translated_input)
            
            # Check if we got an error response
            if "Maaloo, amma kana yaada keessan qabachuuf rakkina qaba" in ai_response:
                await update.message.reply_text(ai_response)
                return
            
            # Translate AI response back to Oromo
            translated_response = await translate_text(ai_response, source_lang="en", target_lang="om")
            logger.info(f"Final Response (Oromo): {translated_response}")
            
            # Send response to user
            await update.message.reply_text(translated_response)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "Dhiifama, rakkina teknikaala qabna. Yeroo muraasa booda irra deebi'aa yaali."
            )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command with Oromo welcome message."""
        welcome_message = "Baga nagaan dhuftan! Ani moodeela afaan keessaniiti. Afaan Oromootiin waan hunda keessan waliin haasa'a. Gaaffii kamiinuu natti qabaa!"
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        help_message = "Gaaffii kamiyyuu afaan Oromootin narraa gaafachuu dandeessu. Ani deebii keessan afaan Oromootiin kennuuf yaala."
        await update.message.reply_text(help_message)

    async def run(self):
        """Run the bot."""
        try:
            application = Application.builder().token(self.token).build()
            
            # Add handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            logger.info("Bot started successfully!")
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

async def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No bot token provided. Set TELEGRAM_BOT_TOKEN environment variable.")
        return

    bot = AIChatBot(TELEGRAM_BOT_TOKEN)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
