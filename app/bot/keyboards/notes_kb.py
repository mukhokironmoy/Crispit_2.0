from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.callbacks import *
from app.db.base import SessionLocal
from app.db.models import ProcessingModes, User, DefaultNotesModes, NotesModes
from app.config.logging import logger

def notes_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Change Mode", callback_data=CB_NOTES_MODES)],
        [InlineKeyboardButton("⬅️ Return to Home", callback_data=CB_NAV_HOME)]
    ])

def back_to_notes_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Return to Notes Page", callback_data=CB_HOME_NOTES)]
    ])

def choose_processing_modes_kb() -> InlineKeyboardMarkup:
    # 1) Establish the session
    session = SessionLocal()

    # 2) Fetch Processing modes
    try:
        processing_modes = session.query(ProcessingModes).all()

        # 3) Create a mapping of each mode with its callback
        processing_mode_mapping = dict({})
        for mode in processing_modes:
            processing_mode_mapping[mode.name] = mode.callback_data

        # 4) Create a list of buttons
        buttons = []
        for mode in processing_mode_mapping.keys():
            buttons.append([InlineKeyboardButton(f"{mode}", callback_data=processing_mode_mapping[mode])])

        buttons.append([InlineKeyboardButton("⬅️ Go Back", callback_data=CB_HOME_NOTES)])
        return InlineKeyboardMarkup(buttons)
    except Exception as e:
        logger.exception(f" DB | Fatal error while creating processing modes keyboard\n {e}")
    finally:
        session.close()

def choose_output_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Text", callback_data=CB_NOTES_OUTPUT_TEXT)],
        [InlineKeyboardButton("📑 Pdf", callback_data=CB_NOTES_OUTPUT_PDF)]
    ])


def choose_notes_modes_kb(output_type, id) -> InlineKeyboardMarkup:
    # 1) Establish the session
    session = SessionLocal()

    try:
        # 2) Get note modes
        default_notes_modes = session.query(DefaultNotesModes).filter(DefaultNotesModes.output_type == output_type).all()
        notes_modes = session.query(NotesModes).filter(NotesModes.user_id == id, NotesModes.output_type == output_type).all()

        # 3) Create list of all note modes
        all_modes = []

        for mode in default_notes_modes:
            all_modes.append({
                "name": mode.name,
                "callback_data":mode.callback_data,
                "output_type":mode.output_type
            })

        for mode in notes_modes:
            all_modes.append({
                "name": mode.name,
                "callback_data":mode.callback_data,
                "output_type":mode.output_type
            })

        # 4) Create button list
        buttons = []
        for mode in all_modes:
            buttons.append([InlineKeyboardButton(mode["name"], callback_data=mode["callback_data"])])
        
        buttons.append([InlineKeyboardButton("⬅️ Go Back", callback_data=CB_NOTES_OUTPUT)])
        
        # 5) Return the keyboard
        return InlineKeyboardMarkup(buttons)
    
    except Exception as e:
        logger.exception(f" DB | Fatal error while creating notes modes keyboard\n {e}")
    finally:
        session.close()

def notes_next_options_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Get notes for another video", callback_data=CB_HOME_NOTES)],
        [InlineKeyboardButton("⬅️ Back to Home", callback_data=CB_NAV_HOME)]
    ])
