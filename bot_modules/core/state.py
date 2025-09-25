from telegram.ext import ContextTypes

# ---- state constants ----
STATE_NONE                 = "NONE"
STATE_AWAIT_TRANSCRIPT_URL = "AWAITING_TRANSCRIPT_URL"
STATE_MAKING_TRANSCRIPT    = "MAKING_TRANSCRIPT"

STATE_AWAIT_NOTES_URL      = "AWAITING_NOTES_URL"
STATE_MAKING_NOTES         = "MAKING_NOTES"

STATE_CHOOSE_NOTES_MODE    = "CHOOSE_NOTES_MODE"


# ---- state helpers ----
def set_state(context: ContextTypes.DEFAULT_TYPE, value: str):
    """Set the current state for this chat session."""
    context.chat_data["state"] = value

def get_state(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Get the current state for this chat session (defaults to NONE)."""
    return context.chat_data.get("state", STATE_NONE)

def clear_state(context: ContextTypes.DEFAULT_TYPE):
    """Reset state back to NONE."""
    context.chat_data["state"] = STATE_NONE
