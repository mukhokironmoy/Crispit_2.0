from telegram import Update
from telegram.ext import ContextTypes
from app.config.logging import logger

# STATES
NONE = "NONE"

AWAITING_TRANSCRIPT_URL = "AWAITING_TRANSCRIPT_URL"
GENERATING_TRANSCRIPT = "GENERATING_TRANSCRIPT"

AWAITING_NOTES_URL = "AWAITING_NOTES_URL"
GENERATING_NOTES = "GENERATING_NOTES"
SENDING_NOTES = "SENDING_NOTES"
CHOOSING_PROCESSING_MODE = "CHOOSING_PROCESSING_MODE"
CHOSSING_OUTPUT_TYPE = "CHOOSING_OUTPUT_TYPE"
CHOOSING_NOTES_MODE = "CHOOSING_NOTES_MODE"

# STATE HELPERS
def set_state(update: Update, context: ContextTypes.DEFAULT_TYPE, value: str):
    context.chat_data["state"] = value
    user = update.effective_user
    logger.info(f"STATE | user_id={user.id} username={user.username} | STATE CHANGED TO {value}")

def get_state(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.chat_data.get("state", NONE)

def clear_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["state"] = NONE
    user = update.effective_user
    logger.info(f"STATE | user_id={user.id} username={user.username} | STATE CLEARED")