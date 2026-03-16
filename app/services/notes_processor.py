# python
from pathlib import Path
import hashlib

# states
from app.bot.state_management import *

# services
from app.services.youtube_data import *
from app.services.gemini_notes import get_notes
from app.services.transcriptor import *

# db and models
from app.db.models import *
from app.db.base import SessionLocal

# handlers
from app.bot.handlers.home import *

# keyboards
from app.bot.keyboards.notes_kb import *

# logger
from app.config.logging import logger

# telegram 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

"""---------------------------------------------------------------------------------------------------------------"""
# GET A PROMPT FINGERPRINT FOR NAMING FILE
def prompt_fingerprint(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]

"""---------------------------------------------------------------------------------------------------------------"""
# SINGLE VIDEO PROCESSOR
async def single_processor(user:User, valid_url_data:dict) -> dict:
    session = SessionLocal()
    
    # GET ESSENTIALS FOR GENERATING NOTES
    #########################################################################
    url = valid_url_data["url"]
    video_id = valid_url_data["video_id"]

    # 1) Get the transcript data
    transcript_path = await fetch_transcript_for_notes(user, video_id)
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()

    # 2) Get the prompt
    logger.info(f"user_id={user.id} username={user.username} | Fetching prompt for mode = {NotesModes.get_name_for_callback(session, user.id, user.current_mode_callback)}")
    prompt = NotesModes.get_prompt_for_callback(session, user.id, user.current_mode_callback)
    logger.info(f"user_id={user.id} username={user.username} | Prompt fetched as:\n\n {prompt}.")
    
    # 3) Set filename
    notes_mode_name = NotesModes.get_name_for_callback(session, user.id, user.current_mode_callback)
    prompt_hash = prompt_fingerprint(prompt)

    filename = f"{video_id}_{notes_mode_name}_{prompt_hash}"

    session.close()

    # 4) Get title
    youtube_data = get_yt_data(url)
    title = youtube_data["Title"]

    # CREATE THE RESULT TEMPLATE
    #########################################################################
    result = {
    "url" : url,
    "video_id": video_id,
    "title": title,
    "notes_path": None,
    "completed": False,
    "reason" : None
    }


    # GENERATE THE NOTES
    #########################################################################
    
    # 1) Get the notes from LLM
    try:
        notes_path = await get_notes(transcript, prompt, filename, title, url)
        logger.info(f"user_id={user.id} username={user.username} | Notes received from LLM.")
        
        # Update result
        result["notes_path"] = notes_path
    
    except Exception as e:
        logger.exception(f"user_id={user.id} username={user.username} | Error while getting notes from LLM:- \n{e}")

        # Update result
        result["reason"] = "LLM generation error"
        return result
        

    # 2) Create db objects
    new_notes_request = VideoRequests(user_id=user.id, video_id=video_id, transcript_path=str(transcript_path), notes_path=str(notes_path), completed=True)
    transcript_cache = ReusableRequests(video_id=video_id, type="Transcript", file_path=str(transcript_path))
    notes_cache = ReusableRequests(video_id=video_id, type="Notes", file_path=str(notes_path))
        
    # 3) Save to db
    try:
        session.add(new_notes_request)
        session.add(transcript_cache)
        session.add(notes_cache)
        session.commit()
        logger.info(f"DB | user_id={user.id} username={user.username} | Notes request and cache data saved to db.")

        # Update result
        result["completed"] = True

        
    except Exception as e:
        session.rollback()
        logger.exception(f"DB | user_id={user.id} username={user.username} |Error while saving notes request and cache data to db. \n{e}")

        # Update result
        result["reason"] = "DB Error"
        return result
        

    finally:
        session.close() 

    
    # RETURN THE RESULTS
    #########################################################################
    logger.info(f"user_id={user.id} username={user.username} | Notes completed for {video_id} successfully")
    logger.info(f"user_id={user.id} username={user.username} | Result generated as {result}")
    return result

    







