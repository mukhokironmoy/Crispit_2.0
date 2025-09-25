# Core package exports
from .logging import logger
from .state import (
    STATE_NONE,
    STATE_AWAIT_TRANSCRIPT_URL,
    STATE_MAKING_TRANSCRIPT,
    STATE_AWAIT_NOTES_URL,
    STATE_MAKING_NOTES,
    STATE_CHOOSE_NOTES_MODE,
    set_state,
    get_state,
    clear_state,
)

__all__ = [
    "logger",
    "STATE_NONE",
    "STATE_AWAIT_TRANSCRIPT_URL",
    "STATE_MAKING_TRANSCRIPT",
    "STATE_AWAIT_NOTES_URL",
    "STATE_MAKING_NOTES",
    "STATE_CHOOSE_NOTES_MODE",
    "set_state",
    "get_state",
    "clear_state",
]
