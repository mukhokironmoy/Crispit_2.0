from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from app.bot.callbacks import *
from app.bot.state_management import *

# handlers
from app.bot.handlers.home import show_home
from app.bot.handlers.transcript import ask_transcript_url, transcript_url_handler
from app.bot.handlers.notes import ask_notes_url, choose_processing_mode, choose_output_type, notes_url_handler

# keyboards
from app.bot.keyboards.home_kb import nav_home_keyboard

async def button_router(update:Update, context:ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()

    if callback.data == CB_NAV_HOME:
        await show_home(update, context)

    elif callback.data == CB_HOME_TRANSCRIPT:
        set_state(update, context, AWAITING_TRANSCRIPT_URL)
        await ask_transcript_url(update, context)
    
    elif callback.data == CB_HOME_NOTES:
        set_state(update, context, AWAITING_NOTES_URL)
        await ask_notes_url(update, context)

    elif callback.data == CB_NOTES_MODES:
        set_state(update, context, CHOOSING_PROCESSING_MODE)
        await choose_processing_mode(update, context)
    
    elif callback.data == CB_NOTES_OUTPUT:
        set_state(update, context, CHOSSING_OUTPUT_TYPE)
        await choose_output_type(update, context)

async def text_router(update:Update, context:ContextTypes.DEFAULT_TYPE):
    state = get_state(context)

    if state == AWAITING_TRANSCRIPT_URL:
        await transcript_url_handler(update, context)
    
    elif state == AWAITING_NOTES_URL:
        await notes_url_handler(update, context)

    else:
        await update.message.reply_text(
            "Sorry! You seem to be in the wrong mode. Please try again!", reply_markup=nav_home_keyboard()
        )

def register(app):
    app.add_handler(CallbackQueryHandler(button_router , pattern=r"^(nav:|home:|notes:)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))