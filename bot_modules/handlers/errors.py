from telegram.ext import ContextTypes
from bot_modules.core.logging import logger

# ---- error handler ----
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    user = getattr(update, "effective_user", None)
    chat = getattr(update, "effective_chat", None)

    logger.error(
        f"⚠️ ERROR | user_id={getattr(user, 'id', None)} username={getattr(user, 'username', None)} "
        f"| chat_id={getattr(chat, 'id', None)} | Exception while handling an update:",
        exc_info=context.error
    )

    # Notify the user something went wrong
    if update and hasattr(update, "effective_message") and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Oops! Something went wrong on my end. The developer’s been notified."
        )

def register(app):
    app.add_error_handler(error_handler)
