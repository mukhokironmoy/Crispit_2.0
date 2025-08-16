import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from log_handler import logger
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import TelegramError

# Load your token
load_dotenv()
BOT_TOKEN = os.getenv("telegram_token")

# log updater
async def log_update_basics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    kind = (
        "callback_query" if update.callback_query else
        "message" if update.message else
        "other"
    )
    textish = (msg.text if msg and msg.text else msg.caption if msg and msg.caption else None)

    logger.info(
        "UPDATE kind=%s | user_id=%s username=%s | chat_id=%s | text=%r",
        kind,
        user.id if user else None,
        user.username if user else None,
        chat.id if chat else None,
        textish
    )

# define button handlers
async def on_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles clicks from InlineKeyboard buttons.
    This is triggered by a CallbackQuery (not a normal message).
    """
    query = update.callback_query
    user = update.effective_user

    # Always acknowledge the button press to stop the client spinner
    await query.answer()

    data = query.data  # this is the callback_data you set on the button
    logger.info("Inline button clicked | user_id=%s data=%r", user.username, data)

    # Route based on callback_data
    if data == "get_transcript":
        await query.message.reply_text(
            "📜 Please send the YouTube link that you would like transcribed:"
        )

    elif data == "get_notes":
        await query.message.reply_text(
            "📝 Please send the YouTube link that you would like to make notes of:"
        )

    else:
        await query.message.reply_text("🤔 I didn’t recognize that action.")

# Define Welcome Keyboard
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

# /start handler function
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Runs when a user sends /start.
    'update' = data about THIS event (user, chat, message).
    'context' = utilities provided by the framework (bot, args, jobs).
    """
    user = update.effective_user          # always safe: best-guess sender
    chat = update.effective_chat          # where it was sent
    msg  = update.effective_message       # the message object (can be None in some update types)

    #Log useful debug info to your terminal
    logger.info(
        "Received /start | user_id=%s username=%s chat_id=%s text=%r",
        user.id, user.username, chat.id, msg.text if msg else None
    )

    # Send a tiny test message so we know the handler ran
    if msg:
        welcome_text = f"👋 Hello!  {user.username}! What would you like to do today?"
        keyboard = build_welcome_keyboard()
        await update.message.reply_text(welcome_text, reply_markup=keyboard)

# help handler function
def build_help_text() -> str:
    return (
        "*Here’s what I can do (so far):*"
        "\n\n"

        "• `/start` — show the welcome screen with the following buttons\n\n"
        "   ◦ *Get Transcript* — Get the transcript of a YouTube video by providing a link.\n"
        "   ◦ *Get Notes* — Get notes for a YouTube video by providing a link"
        "\n\n"

        "• `/help` — show this help\n\n"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user          # always safe: best-guess sender
    chat = update.effective_chat          # where it was sent
    msg  = update.effective_message       # the message object (can be None in some update types)
    
    # Log useful debug info
    logger.info(
        "Received /help | user_id=%s username=%s chat_id=%s text=%r",
        user.id, user.username, chat.id, msg.text if msg else None
    )

    if msg:
        await msg.reply_text(
            build_help_text(),
            parse_mode=ParseMode.MARKDOWN
        )

# echo handler function
async def echo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    # If user typed: /echo hello world
    if context.args:
        text = " ".join(context.args)
        await update.message.reply_text(text)
        logger.info(
            "Received /echo | user_id=%s username=%s chat_id=%s text=%r",
            user.id, user.username, chat.id, msg.text if msg else None
        )
    else:
        await update.message.reply_text("Usage: /echo <text>")

async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only called for plain text (not commands) because of the filter we’ll add
    if update.message and update.message.text:
        await update.message.reply_text(f"Here's what you said : {update.message.text}")


# error handler function
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a message to yourself if needed."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # You can also notify the user something went wrong
    if update and hasattr(update, "effective_message") and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Oops! Something went wrong on my end. The developer’s been notified."
        )

# Main function
def main():
    if not BOT_TOKEN:
        raise RuntimeError("telegram_token is missing. Check .env and that your venv is active.")

    app = Application.builder().token(BOT_TOKEN).build()

    # Wire the /start command to your handler function
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(on_inline_button))
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("echo", echo_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_text))
    app.add_handler(MessageHandler(filters.ALL, log_update_basics), group=1)

    




    logger.info("✅ Bot is running (long polling). Press Ctrl+C to stop.")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
