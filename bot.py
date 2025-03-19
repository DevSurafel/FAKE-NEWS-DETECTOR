import os
import logging
from dotenv import load_dotenv
load_dotenv()
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
import requests
import asyncio
import nest_asyncio
import re
from googletrans import Translator

nest_asyncio.apply()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Hugging Face Inference API credentials
API_TOKEN_AI_MODEL = os.getenv("HF_AI_MODEL_API_TOKEN")
API_URL_AI_MODEL = os.getenv("HF_AI_MODEL_API_URL")

headers_ai = {"Authorization": f"Bearer {API_TOKEN_AI_MODEL}"}

# Initialize translator
translator = Translator()

user_conversation_history = {}

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using googletrans."""
    try:
        translation = translator.translate(text, src=source_lang, dest=target_lang)
        translated_text = translation.text
        logger.info(f"Successfully translated from {source_lang} to {target_lang}: {translated_text}")
        return translated_text
    except Exception as e:
        logger.error(f"Translation error from {source_lang} to {target_lang}: {e}")
        return text  # Return original text if translation fails

async def get_ai_response(user_id, text: str, max_retries=3, retry_delay=2) -> str:
    """Get AI response with retry logic and conversation history."""
    retries = 0
    while retries < max_retries:
        try:
            prompt = f"User: {text}\nAssistant:"
            response = requests.post(API_URL_AI_MODEL, headers=headers_ai, json={"inputs": prompt})
            response.raise_for_status()
            ai_response = response.json()[0]['generated_text']
            ai_response = ai_response.split("Assistant:")[-1].strip()
            ai_response = re.sub(r"User:.*", "", ai_response).strip()

            if user_id in user_conversation_history:
                user_conversation_history[user_id].append(f"User: {text} Assistant: {ai_response}")
            else:
                user_conversation_history[user_id] = [f"User: {text} Assistant: {ai_response}"]
            user_conversation_history[user_id] = user_conversation_history[user_id][-5:]

            logger.info(f"AI Response (English): {ai_response}")
            return ai_response
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Model API error (retry {retries + 1}/{max_retries}): {e}")
            retries += 1
            if retries < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                return "Maaloo, amma kana yaada keessan qabachuuf rakkina qaba."

class AIChatBot:
    def __init__(self, token: str):
        self.token = token

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        user = update.message.from_user
        user_text = update.message.text
        user_id = user.id

        if re.search(r"(sexy|porn|nude)", user_text, re.IGNORECASE):
            await update.message.reply_text("Gaaffii wanta tola hin oolleef deebii hin kennu.")
            return

        await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")

        logger.info(f"User Input (Oromo): {user_text}")
        translated_input = await translate_text(user_text, source_lang="om", target_lang="en")
        if translated_input == user_text:
            logger.warning("Translation from Oromo to English failed, using original text.")
            translated_input = user_text  # Fallback to original Oromo text

        logger.info(f"Translated Input (Oromo to English): {translated_input}")
        ai_response = await get_ai_response(user_id, translated_input)
        if ai_response == "Maaloo, amma kana yaada keessan qabachuuf rakkina qaba.":
            await update.message.reply_text(ai_response)
            return

        translated_response = await translate_text(ai_response, source_lang="en", target_lang="om")
        if translated_response == ai_response:
            logger.warning("Translation from English to Oromo failed.")
            translated_response = "Rakkina dubbii qaba, deebii hin argamne."

        logger.info(f"Final Response (Oromo): {translated_response}")
        await update.message.reply_text(translated_response)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command with Oromo welcome message."""
        welcome_message = "Baga nagaan dhuftan! Ani Grok 3, xAI'n ijaarrame. Afaan Oromootin waan hunda keessan waliin haasa'a. Gaaffii kamiinuu natti qabaa!"
        await update.message.reply_text(welcome_message)

    async def run(self):
        """Run the bot."""
        try:
            application = Application.builder().token(self.token).build()
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            logger.info("Bot started successfully!")
            await application.run_polling()
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

async def main():
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("No bot token provided. Set TELEGRAM_BOT_TOKEN environment variable.")
        return

    bot = AIChatBot(TOKEN)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
