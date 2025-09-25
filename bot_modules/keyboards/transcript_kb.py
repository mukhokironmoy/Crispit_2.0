from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from bot_modules.keyboards.navigation_kb import CB_NAV_HOME

def build_transcript_options_keyboard(labels: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(label, callback_data=f"tr:pick:{i}")] for i, label in enumerate(labels)]
    rows.append([InlineKeyboardButton("⬅️ Go back", callback_data=CB_NAV_HOME)])
    return InlineKeyboardMarkup(rows)

def build_post_transcript_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Home", callback_data=CB_NAV_HOME)]])
