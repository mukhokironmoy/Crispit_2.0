from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.callbacks import *

def back_to_transcript_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Return to Notes Page", callback_data=CB_HOME_TRANSCRIPT)]
    ])

def transcript_next_options_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Transcribe another video", callback_data=CB_HOME_TRANSCRIPT)],
        [InlineKeyboardButton("⬅️ Back to Home", callback_data=CB_NAV_HOME)]
    ])