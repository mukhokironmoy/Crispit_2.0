from pathlib import Path
from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

from bot_modules.core.logging import logger
from bot_modules.core.state import clear_state, set_state
from bot_modules.keyboards.home_kb import build_welcome_keyboard
from bot_modules.keyboards.navigation_kb import go_back
from bot_modules.keyboards.notes_kb import build_notes_prompt_keyboard

# ---- callback constants ----
CB_HOME_TRANSCRIPT = "home:transcript"
CB_HOME_NOTES      = "home:notes"
CB_HOME_HELP       = "home:help"
CB_NAV_HOME        = "nav:home"
CB_CHOOSE_NOTES_MODE = "notes:choose_notes_mode"
CB_BACK_TO_NOTES_MODES = "nav:back_to_notes_modes"


# ---- home text ----
def build_home_text() -> str:
    return "🏠 *Crispit Bot — Home*\nWhat would you like to do today?"


# ---- show home panel ----
async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(context)

    # defaults
    context.chat_data.setdefault("notes_mode", "Crispit Default")
    context.chat_data.setdefault("notes_prompt_path", Path(r"telegram_in_data\crispit_default_prompt.txt"))
    context.chat_data.setdefault("available_modes", [
        {
            "name": "Crispit Default",
            "path": Path(r"telegram_in_data\crispit_default_prompt.txt"),
            "built_in": True
        },
        {
            "name": "LLM Default",
            "path": Path(r"telegram_in_data\LLM_default_prompt.txt"),
            "built_in": True
        }
    ])

    user = update.effective_user
    welcome_text = f"*Hello {user.username}! Welcome to Crispit!*\n\n" + build_home_text()
    markup = build_welcome_keyboard()

    # If called from /start or /menu (a message), send new panel
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    # If called from a button tap, edit the existing panel
    elif update.callback_query:
        q = update.callback_query
        await q.answer()
        await q.message.edit_text(welcome_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)


# ---- handler for home buttons ----
async def on_home_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = update.effective_user
    chat = update.effective_chat

    await q.answer()
    data = q.data  

    if data == CB_HOME_TRANSCRIPT:
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User in Transcript Route. Awaiting url…")
        from bot_modules.handlers.transcript import show_transcript_prompt
        await show_transcript_prompt(q, context)

    elif data == CB_HOME_NOTES:
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User in Notes Route. Awaiting url…")
        from bot_modules.handlers.notes import show_notes_prompt
        await show_notes_prompt(q, context)

    elif data == CB_HOME_HELP:
        from bot_modules.handlers.help import help_panel
        await help_panel(q)

    else:
        await q.message.reply_text("🤔 I didn’t recognize that action.")


# ---- navigation: go back buttons ----
async def go_back_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == CB_NAV_HOME:
        await show_home(update, context)

    elif q.data == CB_BACK_TO_NOTES_MODES:
        from bot_modules.handlers.notes import show_notes_modes
        await show_notes_modes(q, context)


# ---- register handlers ----
def register(app):
    app.add_handler(CommandHandler("start", show_home))
    app.add_handler(CallbackQueryHandler(on_home_buttons, pattern=r"^home:"))
    app.add_handler(CallbackQueryHandler(go_back_buttons, pattern=r"^nav:"))
