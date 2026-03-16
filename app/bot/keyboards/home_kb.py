from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.callbacks import *

def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖨️ Get Transcript", callback_data=CB_HOME_TRANSCRIPT)],
        [InlineKeyboardButton("📝 Get Notes", callback_data=CB_HOME_NOTES)],
        [InlineKeyboardButton("ℹ️ Help", callback_data=CB_HOME_HELP)],        
    ])

def nav_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Return to Home", callback_data=CB_NAV_HOME)]
    ])