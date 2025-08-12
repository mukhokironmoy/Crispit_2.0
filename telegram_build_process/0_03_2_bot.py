import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from log_handler import logger
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes

# 1) Load your token
load_dotenv()
BOT_TOKEN = os.getenv("telegram_token")

#Define Welcome Keyboard
def build_welcome_keyboard() -> InlineKeyboardMarkup:
    """
    Returns an inline keyboard with one 'Get Started' button.
    Inline keyboards appear under the message and can have callback actions.
    """
    keyboard_layout = [
        [InlineKeyboardButton("Get Transcript", callback_data="get_transcript")],
        [InlineKeyboardButton("Get Notes", callback_data="get_notes")]

    ]
    return InlineKeyboardMarkup(keyboard_layout)

# 2) Write your FIRST handler function
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Runs when a user sends /start.
    'update' = data about THIS event (user, chat, message).
    'context' = utilities provided by the framework (bot, args, jobs).
    """
    user = update.effective_user          # always safe: best-guess sender
    chat = update.effective_chat          # where it was sent
    msg  = update.effective_message       # the message object (can be None in some update types)

    # Log useful debug info to your terminal
    logger.info(
        "Received /start | user_id=%s username=%s chat_id=%s text=%r",
        user.id, user.username, chat.id, msg.text if msg else None
    )

    # Send a tiny test message so we know the handler ran
    if msg:
        welcome_text = f"👋 Hello!  {user.username}! What would you like to do today?"
        keyboard = build_welcome_keyboard()
        await update.message.reply_text(welcome_text, reply_markup=keyboard)


# 4) Build the Application and register the handler
def main():
    if not BOT_TOKEN:
        raise RuntimeError("telegram_token is missing. Check .env and that your venv is active.")

    app = Application.builder().token(BOT_TOKEN).build()

    # Wire the /start command to your handler function
    app.add_handler(CommandHandler("start", start))

    logger.info("✅ Bot is running (long polling). Press Ctrl+C to stop.")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
