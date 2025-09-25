import os
from dotenv import load_dotenv
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters

from bot_modules.core.logging import logger
from bot_modules.handlers import home, transcript, notes, help, echo, misc, errors


def create_app():
    """Build and return a configured Telegram Application."""
    load_dotenv()
    BOT_TOKEN = os.getenv("telegram_token")

    if not BOT_TOKEN:
        raise RuntimeError("telegram_token is missing. Check .env and venv.")

    app = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()

    # ---- logging handlers (group=-1 so they run before others) ----
    async def log_all_messages(update, context):
        if update.effective_message:
            u = update.effective_user
            c = update.effective_chat
            m = update.effective_message
            textish = m.text or m.caption if (m.text or m.caption) else None
            logger.info("MSG | user_id=%s username=%s | chat_id=%s | text=%r",
                        getattr(u, "id", None), getattr(u, "username", None),
                        getattr(c, "id", None), textish)

    async def log_all_commands(update, context):
        if update.effective_message:
            u = update.effective_user
            c = update.effective_chat
            m = update.effective_message
            logger.info("CMD | user_id=%s username=%s | chat_id=%s | command=%r",
                        getattr(u, "id", None), getattr(u, "username", None),
                        getattr(c, "id", None), getattr(m, "text", None))

    async def log_all_callbacks(update, context):
        if update.callback_query:
            q = update.callback_query
            u = update.effective_user
            c = update.effective_chat
            logger.info("CBQ | user_id=%s username=%s | chat_id=%s | data=%r",
                        getattr(u, "id", None), getattr(u, "username", None),
                        getattr(c, "id", None), getattr(q, "data", None))

    app.add_handler(MessageHandler(filters.COMMAND, log_all_commands), group=-1)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, log_all_messages), group=-1)
    app.add_handler(CallbackQueryHandler(log_all_callbacks), group=-1)

    # ---- register feature handlers ----
    home.register(app)
    transcript.register(app)
    notes.register(app)
    help.register(app)
    echo.register(app)
    misc.register(app)
    errors.register(app)

    logger.info("✅ Crispit Bot app created successfully")
    return app
