import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from log_handler import logger
from get_transcript import get_transcript
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import TelegramError
import re
"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# LOADING TOKEN
load_dotenv()
BOT_TOKEN = os.getenv("telegram_token")

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# LOGGER FUNCTIONS

# Logs only normal messages (no commands)
async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        u = update.effective_user
        c = update.effective_chat
        m = update.effective_message
        textish = m.text if m.text else m.caption if m.caption else None

        logger.info(
            "MSG | user_id=%s username=%s | chat_id=%s | text=%r",
            u.id if u else None,
            u.username if u else None,
            c.id if c else None,
            textish
        )

# Logs only commands
async def log_all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        u = update.effective_user
        c = update.effective_chat
        m = update.effective_message
        logger.info(
            "CMD | user_id=%s username=%s | chat_id=%s | command=%r",
            u.id if u else None,
            u.username if u else None,
            c.id if c else None,
            m.text
        )

# Logs all button presses
async def log_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        q = update.callback_query
        u = update.effective_user
        c = update.effective_chat
        logger.info(
            "CBQ | user_id=%s username=%s | chat_id=%s | data=%r",
            u.id if u else None,
            u.username if u else None,
            c.id if c else None,
            q.data
        )

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# STATE MANAGEMENT

# ---- tiny state map ----
STATE_NONE                 = "NONE"
STATE_AWAIT_TRANSCRIPT_URL = "AWAITING_TRANSCRIPT_URL"
STATE_AWAIT_NOTES_URL      = "AWAITING_NOTES_URL"

def set_state(context: ContextTypes.DEFAULT_TYPE, value: str):
    context.chat_data["state"] = value

def get_state(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.chat_data.get("state", STATE_NONE)

def clear_state(context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["state"] = STATE_NONE

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# STARTUP AND /start HANDLER FUNCTION

# ---- callbacks (namespaced) ----
CB_HOME_TRANSCRIPT = "home:transcript"
CB_HOME_NOTES      = "home:notes"
CB_HOME_HELP       = "home:help"
CB_NAV_HOME        = "nav:home"

# building the welcome keyboard
def build_welcome_keyboard() -> InlineKeyboardMarkup:
    keyboard_layout = [
        [InlineKeyboardButton("Get Transcript", callback_data= CB_HOME_TRANSCRIPT)],
        [InlineKeyboardButton("Get Notes", callback_data=CB_HOME_NOTES)],
        [InlineKeyboardButton("Help", callback_data=CB_HOME_HELP)]

    ]
    return InlineKeyboardMarkup(keyboard_layout)

# setting the home text
def build_home_text() -> str:
    return "🏠 *Crispit Bot — Home*\nWhat would you like to do today?"

# defining home
async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(context)
    user = update.effective_user          # always safe: best-guess sender
    chat = update.effective_chat          # where it was sent
    msg  = update.effective_message       # the message object (can be None in some update types)

    welcome_text = f"*Hello {user.username}! Welcome to Crispit!*\n\n" + build_home_text()
    markup = build_welcome_keyboard()


    # If this came from /start or /menu (a message), send a new panel.
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN) 

    # If this came from a button tap (a callback), edit the existing panel (updates the menu in place)
    elif update.callback_query:
        q = update.callback_query
        await q.answer()
        await q.message.edit_text(welcome_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN) 

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# BUTTON FUNCTIONS

# return home button
def go_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Go back", callback_data = CB_NAV_HOME)]])

# response for transcript button
async def show_transcript_prompt(q, context):
    set_state(context, STATE_AWAIT_TRANSCRIPT_URL)  # q is a CallbackQuery; PTB lets you pass it as context in our helper
    await q.message.edit_text(
        "📜 Please send the YouTube link you want transcribed: ",
        reply_markup = go_back()
    )

# response for notes button
async def show_notes_prompt(q, context):
    set_state(context, STATE_AWAIT_NOTES_URL)
    await q.message.edit_text(
        "📝 Please send the YouTube link you want summarized into notes: ",
        reply_markup = go_back()
    )

# diplay for help button
async def help_panel(q):
    text = (
        "*Here’s what I can do (so far):*"
        "\n\n"

        "• `/start` — show the welcome screen with the following buttons\n\n"
        "   ◦ *Get Transcript* — Get the transcript of a YouTube video by providing a link.\n"
        "   ◦ *Get Notes* — Get notes for a YouTube video by providing a link"
        "\n\n"

        "• `/help` — show this help\n\n"
    )
    await q.message.edit_text(text, reply_markup=go_back(), parse_mode = ParseMode.MARKDOWN)

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# BUTTON HANDLERS

# handler for home page
async def on_home_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query

    await q.answer()
    data = q.data  

    # Route based on callback_data
    if data == CB_HOME_TRANSCRIPT:
        await show_transcript_prompt(q, context)

    elif data == CB_HOME_NOTES:
        await show_notes_prompt(q, context)

    elif data == CB_HOME_HELP:
        await help_panel(q, context)

    else:
        await q.message.reply_text("🤔 I didn’t recognize that action.")

# handler for go back
async def go_back_buttons(update:Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query

    await q.answer()

    if q.data == CB_NAV_HOME:
        await show_home(update, context)

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# COMMANDS

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

    if msg:
        await msg.reply_text(
            build_help_text(),
            reply_markup=go_back(),
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

    else:
        await update.message.reply_text("Usage: /echo <text>")


# Receiving text handler
async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    # Only called for plain text (not commands) because of the filter we’ll add
    if update.message and update.message.text:
        text = update.message.text.strip()
        state = get_state(context)

        # Awaiting transcript link
        if state == STATE_AWAIT_TRANSCRIPT_URL:            
            url = text

            # Placeholder: store somewhere if you like
            context.chat_data["last_transcript_url"] = url

            # Confirm 
            await update.message.reply_text(f"✅ Got the link for transcript : {url}")
            clear_state(context)
            await show_home(update, context)
            return
        
        # Awaiting notes link
        if state == STATE_AWAIT_NOTES_URL:            
            url = text

            # Placeholder: store somewhere if you like
            context.chat_data["last_notes_url"] = url

            # Confirm 
            await update.message.reply_text(f"✅ Got the link for notes : {url}")
            clear_state(context)
            await show_home(update, context)
            return
        
        # Default echo behaviour
        await update.message.reply_text(f"Here's what you said : {text}")          


# photo handler functions
async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    photos = msg.photo  # list[PhotoSize], smallest → largest

    if not photos:
        return  # safety

    largest = photos[-1]  # best quality
    caption = msg.caption or "(no caption)"

    info = (
        "📸 Got your photo!\n"
        f"- Size: {largest.width}×{largest.height}\n"
        f"- File ID ends with: …{str(largest.file_id)[-6:]}\n"
        f"- Caption: {caption}"
    )
    await msg.reply_text(info)

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
#ERROR HANDLING

# error handler function
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a message to yourself if needed."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # You can also notify the user something went wrong
    if update and hasattr(update, "effective_message") and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Oops! Something went wrong on my end. The developer’s been notified."
        )

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# MAIN FUNCTION
def main():
    if not BOT_TOKEN:
        raise RuntimeError("telegram_token is missing. Check .env and that your venv is active.")

    app = Application.builder().token(BOT_TOKEN).build()

    # log handlers
    app.add_handler(MessageHandler(filters.COMMAND, log_all_commands), group=-1)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, log_all_messages), group=-1)
    app.add_handler(CallbackQueryHandler(log_all_callbacks), group=-1)

    # command handlers
    app.add_handler(CommandHandler("start", show_home))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("echo", echo_cmd))


    # button handlers
    app.add_handler(CallbackQueryHandler(on_home_buttons, pattern=r"^home:"))
    app.add_handler(CallbackQueryHandler(go_back_buttons, pattern=r"^nav:"))

    # error handlers
    app.add_error_handler(error_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))


    logger.info("✅ Bot is running (long polling). Press Ctrl+C to stop.")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
