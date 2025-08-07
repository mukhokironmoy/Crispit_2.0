# bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import os
from get_transcript import transcript

#load the bot_token
load_dotenv()
BOT_TOKEN = os.getenv('telegram_token')

# Handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
    [InlineKeyboardButton("📄 Get Transcript", callback_data="get_transcript")],
    [InlineKeyboardButton("📝 Get Notes", callback_data="get_notes")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("👋 Welcome to Crispit! What would you like to do?", reply_markup=reply_markup)

# Handle /get_transcript command
async def get_transcript(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #ask for url
    await update.message.reply_text("Enter the url of the video you would like transcribed: ")

    video_url = update.message.text
    transcript(video_url)

    #send message
    await update.message.reply_text(f"Here's the transcript for your video transcript: ")

    #send file
    await update.message.reply_document(document=open("data/transcript.txt", "rb"))


# Handle /get_notes command
async def get_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #dummy
    await update.message.reply_text("Here are your notes!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    print("Bot is running....")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_transcript))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes))
    app.run_polling()
