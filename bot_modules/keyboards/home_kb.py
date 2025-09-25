from telegram import InlineKeyboardMarkup, InlineKeyboardButton

CB_HOME_TRANSCRIPT = "home:transcript"
CB_HOME_NOTES      = "home:notes"
CB_HOME_HELP       = "home:help"

def build_welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Get Transcript", callback_data=CB_HOME_TRANSCRIPT)],
        [InlineKeyboardButton("Get Notes", callback_data=CB_HOME_NOTES)],
        [InlineKeyboardButton("Help", callback_data=CB_HOME_HELP)]
    ])
