import os
import asyncio
import logging
import tempfile
from dotenv import load_dotenv
import edge_tts

from telegram import Update
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

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Default Voice
VOICE = "en-US-AriaNeural"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nSend me any text and I will convert it to speech 🎧"
    )

# TTS function
async def text_to_speech(text: str):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        file_path = f.name

    communicate = edge_tts.Communicate(text=text, voice=VOICE)
    await communicate.save(file_path)

    return file_path

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if len(text) > 1000:
        await update.message.reply_text("❌ Text too long (max 1000 chars)")
        return

    msg = await update.message.reply_text("⏳ Converting to voice...")

    try:
        audio_path = await text_to_speech(text)

        await update.message.reply_voice(voice=open(audio_path, "rb"))

        os.remove(audio_path)

        await msg.delete()

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ Error generating voice")

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
