from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from bot_modules.keyboards.navigation_kb import CB_NAV_HOME

CB_CHOOSE_NOTES_MODE = "notes:choose_notes_mode"
CB_HOME_NOTES        = "home:notes"

def build_notes_prompt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Choose mode", callback_data=CB_CHOOSE_NOTES_MODE)],
        [InlineKeyboardButton("⬅️ Go back", callback_data=CB_NAV_HOME)]
    ])


def build_notes_modes_keyboard(context) -> InlineKeyboardMarkup:
    rows = []
    modes = context.chat_data.get("available_modes", [])

    for i, mode in enumerate(modes):
        rows.append([InlineKeyboardButton(f"📒 {mode['name']}", callback_data=f"mode:pick:{i}")])

    rows.append([InlineKeyboardButton("------", callback_data="mode:blank")])
    rows.append([InlineKeyboardButton("➕ Add Custom Mode", callback_data="mode:add")])
    rows.append([InlineKeyboardButton("⬅️ Go back", callback_data=CB_HOME_NOTES)])
    return InlineKeyboardMarkup(rows)


def build_post_notes_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Get notes for another video", callback_data=CB_HOME_NOTES)],
        [InlineKeyboardButton("⬅️ Back to Home", callback_data=CB_NAV_HOME)]
    ])
