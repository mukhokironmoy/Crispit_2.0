from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler
from telegram.constants import ParseMode
from app.bot.state_management import *
from app.db.base import SessionLocal
from app.db.models import User
from app.bot.keyboards.home_kb import nav_home_keyboard

async def show_home(update:Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(update, context)
    user = update.effective_user

    # 1) Establishing the session
    session = SessionLocal()

    # 2) Check for existing user
    existing_user = session.query(User).filter(User.id == user.id).first()

    if existing_user is None:
        logger.info(f" DB | user_id={user.id} username={user.username} | user does not exist in system. Registering now....")
        
        # 2.1) Creating new user object
        new_user = User(
            id = user.id,
            username = user.username
        )

        # 2.2) Adding new user to db
        try:
            session.add(new_user)
            session.commit()
            logger.info(f" DB | user_id={user.id} username={user.username} | user registered successfully!")
            existing_user = session.query(User).filter(User.id == user.id).first()

        # 2.3) Fallback  
        except Exception as e:
            session.rollback()
            logger.exception(f" DB | Fatal error during user registration")

            error_text = (
            "⚠️ *Something went wrong while setting things up.*\n\n"
            "Please try again in a moment."
            )

            if update.message:
                await update.message.reply_text(error_text, reply_markup=nav_home_keyboard, parse_mode=ParseMode.MARKDOWN)
            elif update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.edit_text(error_text, reply_markup=nav_home_keyboard, parse_mode=ParseMode.MARKDOWN)
            
            return
        
        finally:
            session.close()

    # # 3) Updating the chat context with the user data
    # context.chat_data["user"] = existing_user
    
    # 4) Set the welcome text
    welcome_text = f"Greetings {user.username}! Welcome to Crispit!\n\n🏠 *Crispit Bot — Home*\nWhat would you like to do today?"
    
    # 5) Set the buttons 
    from app.bot.keyboards.home_kb import welcome_keyboard

    # 6.1) If called from a command => send a new message
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup= welcome_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    # 6.2) If called from a button tap => edit the current message
    elif update.callback_query:
        callback = update.callback_query
        await callback.answer()
        await callback.message.edit_text(welcome_text, reply_markup = welcome_keyboard(), parse_mode = ParseMode.MARKDOWN)


# Registering the handlers
def register(app):
    app.add_handler(CommandHandler("start", show_home))