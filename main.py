import os
import logging
import tempfile
from dotenv import load_dotenv
import edge_tts

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Load ENV
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# User data
user_lang = {}
user_gender = {}

# Voices (Language + Gender)
VOICES = {
    ("English", "Male"): "en-US-GuyNeural",
    ("English", "Female"): "en-US-AriaNeural",
    ("Bangla", "Female"): "bn-BD-NabanitaNeural",
    ("Bangla", "Male"): "bn-BD-PradeepNeural"  # fallback if works
}

# Keyboards
lang_kb = ReplyKeyboardMarkup([["English", "Bangla"]], resize_keyboard=True)
gender_kb = ReplyKeyboardMarkup([["Male", "Female"]], resize_keyboard=True)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nSelect Language:",
        reply_markup=lang_kb
    )

# TTS
async def text_to_speech(text: str, voice: str):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        file_path = f.name

    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(file_path)

    return file_path

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text

    # Language select
    if text in ["English", "Bangla"]:
        user_lang[user_id] = text
        await update.message.reply_text(
            f"✅ Language set to {text}\nNow select Gender:",
            reply_markup=gender_kb
        )
        return

    # Gender select
    if text in ["Male", "Female"]:
        user_gender[user_id] = text
        await update.message.reply_text(f"✅ Gender set to {text}")
        return

    # Check setup
    if user_id not in user_lang:
        await update.message.reply_text("⚠️ Select language first")
        return

    if user_id not in user_gender:
        await update.message.reply_text("⚠️ Select gender first")
        return

    if len(text) > 1000:
        await update.message.reply_text("❌ Text too long (max 1000 chars)")
        return

    voice = VOICES.get((user_lang[user_id], user_gender[user_id]))

    msg = await update.message.reply_text("⏳ Converting to voice...")

    try:
        audio_path = await text_to_speech(text, voice)

        with open(audio_path, "rb") as audio:
            await update.message.reply_voice(voice=audio)

        os.remove(audio_path)
        await msg.delete()

    except Exception as e:
        logging.exception("Error:")
        await update.message.reply_text("❌ Error generating voice")

# Main
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
