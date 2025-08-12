# bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
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

# Handle button clicks
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query      # Get the callback object
    await query.answer()               # Acknowledge the button press (required)

    if query.data == "get_transcript":
        # Store the user's intent in context
        context.user_data["expecting"] = "transcript"
        await query.message.reply_text("📥 Please send the YouTube link you'd like transcribed.")

    elif query.data == "get_notes":
        # Store dummy intent
        context.user_data["expecting"] = "notes"
        await query.message.reply_text("📝 This feature is coming soon!")


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


#Practice

#Understanding interactions
async def debug_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)  # Print the whole update object


if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    print("Bot is running....")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button_click))
    app.add_handler(MessageHandler(filters.ALL, debug_update))
    app.run_polling()
