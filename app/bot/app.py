import os
from dotenv import load_dotenv
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, CommandHandler
from app.config.logging import logger
from app.bot import router
from app.bot.handlers import home, transcript, notes
import asyncio

def create_app():
    
    # Load the telegram bot token
    load_dotenv()
    BOT_TOKEN = os.getenv("telegram_token")

    if not BOT_TOKEN:
        raise RuntimeError("telegram_token is missing. Check .env and venv.")
    
    # Create the app
    app = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()

    ''' ------------------------------------------------------------------------------------------------ '''
    # SETTING UP THE LOGGERS

    # Log Handler 1 : for logging all messages
    async def log_all_messages(update, context):
        if update.effective_message:
            user = update.effective_user
            chat = update.effective_chat
            message = update.effective_message

            text = message.text or message.caption if (message.text or message.caption) else None

        logger.info(
            "MSG | user_id=%s username=%s | text=%r",
            user.id,
            user.username,
            text
        )

    # Registering Log Handler 1
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, log_all_messages), group=-1)

    # Log Handler 2 : for logging all commands
    async def log_all_commands(update, context):
        if update.effective_message:
            user = update.effective_user
            chat = update.effective_chat
            message = update.effective_message

            command_text = message.text

            logger.info(
                "CMD | user_id=%s username=%s | command=%r",
                user.id,
                user.username,
                command_text
            )
    
    # Registering Log Handler 2
    app.add_handler(MessageHandler(filters.COMMAND, log_all_commands),  group=-1)

    # Log Handler 3 : for logging all button callbacks
    async def log_all_callbacks(update, context):
        if update.effective_message:
            user = update.effective_user
            chat = update.effective_chat
            q = update.callback_query

            logger.info(
                "CBQ | user_id=%s username=%s | data=%r",
                user.id,
                user.username,
                q.data
            )

    # Registering Log Handler 3
    app.add_handler(CallbackQueryHandler(log_all_callbacks), group=-1)

    # Error Handler
    def telegram_error_handler(update, context):
        logger.exception(
            "Telegram error occurred",
            exc_info=context.error
        )

    app.add_error_handler(telegram_error_handler)

    # async def heartbeat():
    #     while True:
    #         logger.info("HEARTBEAT | loop alive")
    #         await asyncio.sleep(5)

    # app.create_task(heartbeat())

    ''' ------------------------------------------------------------------------------------------------ '''

    # Registering all handlers
    home.register(app)   
    router.register(app) 
    notes.register(app)
    # transcript.register(app)

    logger.info("✅ Crispit Bot setup successfully!")
    return app