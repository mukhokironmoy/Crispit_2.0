from telegram import InlineKeyboardMarkup, InlineKeyboardButton

CB_NAV_HOME = "nav:home"

def go_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Go back", callback_data=CB_NAV_HOME)]])
