from pathlib import Path
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ContextTypes

from bot_modules.core.logging import logger
from bot_modules.core.state import (
    set_state, clear_state,
    STATE_AWAIT_NOTES_URL, STATE_CHOOSE_NOTES_MODE
)
from bot_modules.keyboards.navigation_kb import CB_NAV_HOME
from bot_modules.keyboards.notes_kb import (
    build_notes_prompt_keyboard,
    build_notes_modes_keyboard,
    build_post_notes_keyboard
)


# ---- callback constants ----
CB_HOME_NOTES       = "home:notes"
CB_CHOOSE_NOTES_MODE = "notes:choose_notes_mode"


# ---- show notes prompt (called from home) ----
async def show_notes_prompt(q, context):
    clear_state(context)
    set_state(context, STATE_AWAIT_NOTES_URL)

    await q.message.edit_text(
        f"[CURRENT MODE: {context.chat_data['notes_mode'].upper()}]\n\n📜 Please send the YouTube link you want to make notes of:",
        reply_markup=build_notes_prompt_keyboard()
    )


# ---- handler for notes buttons ----
async def on_notes_buttons(update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data
    user = update.effective_user
    chat = update.effective_chat

    if data == CB_CHOOSE_NOTES_MODE:
        logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Choosing notes mode")
        await show_notes_modes(q, context)

    elif data == CB_NAV_HOME:
        from bot_modules.handlers.home import show_home
        await show_home(update, context)

    elif data == "notes:make_notes":
        await show_notes_prompt(q, context)


# ---- show notes modes ----
async def show_notes_modes(q, context):
    set_state(context, STATE_CHOOSE_NOTES_MODE)

    await q.message.edit_text(
        f"[CURRENT MODE: {context.chat_data['notes_mode'].upper()}]\n\n📝 Please choose the mode of notes:",
        reply_markup=build_notes_modes_keyboard(context)
    )


# ---- handler for mode selection ----
async def on_notes_modes_buttons(update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data
    user = update.effective_user
    chat = update.effective_chat

    if data.startswith("mode:pick:"):
        try:
            idx = int(data.split(":")[-1])
        except ValueError:
            await q.answer("Invalid option.", show_alert=True)
            return

        modes = context.chat_data.get("available_modes", [])
        if not modes or idx < 0 or idx >= len(modes):
            await q.answer("That option is no longer available.", show_alert=True)
            logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Invalid mode option")
            return

        chosen_mode = modes[idx]
        context.chat_data["notes_mode"] = chosen_mode["name"]
        context.chat_data["notes_prompt_path"] = chosen_mode["path"]

        logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | User chose mode: {chosen_mode}")
        clear_state(context)

        await show_notes_prompt(q, context)

    elif data == "mode:add":
        await q.message.edit_text("➕ Feature not implemented yet. Here you’ll be able to add a custom mode.")


# ---- register handlers ----
def register(app):
    app.add_handler(CallbackQueryHandler(on_notes_buttons, pattern=r"^notes:"))
    app.add_handler(CallbackQueryHandler(on_notes_modes_buttons, pattern=r"^mode:"))
