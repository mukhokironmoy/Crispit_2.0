from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from app.bot.handlers.home import show_home
from app.bot.keyboards.home_kb import nav_home_keyboard
from app.bot.keyboards.transcript_kb import *
from app.bot.state_management import *
from app.config.logging import logger
from app.services.transcriptor import *
from app.services.youtube_data import get_video_id, get_yt_data
from app.db.base import SessionLocal
from app.db.models import *

# FUNCTION TO ASK USER FOR URL
async def ask_transcript_url(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text(
        "🔗 Please send the YouTube link you want transcribed:",
        reply_markup= nav_home_keyboard()
    )

"""---------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO RECEIVER THE URL
async def transcript_url_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    # Fetch the user
    user = update.effective_user

    # Check state
    state = get_state(context)
    if state != AWAITING_TRANSCRIPT_URL:
        logger.info(f" STATE | user_id={user.id} username={user.username} | Access from illegal state")
        await show_home(update, context)
        return
    
    # Fetch url
    url = update.message.text
    
    # Get youtube data
    youtube_data = get_yt_data(url)

    # Get video id
    try:
        video_id = get_video_id(url)        
    except Exception as e:
        logger.error(f" user_id={user.id} username={user.username} | Invalid URL sent by user.")
        await update.message.reply_text(
            f"⚠️ {e}. Please enter a valid YouTube url.", reply_markup = back_to_transcript_kb()
        )
        return
    
    # Check if a request exists for the same video id
    session = SessionLocal()
    prev_request = session.query(ReusableRequests).filter(
        (ReusableRequests.video_id == video_id) & 
        (ReusableRequests.type=="Transcript")
    ).first()
    
    # Check if the transcript file exists
    if prev_request:
        transcript_file = Path(prev_request.file_path)
        
        if transcript_file.exists():
            logger.info(f" user_id={user.id} username={user.username} | Transcript exists in db and in storage")
           
            # Send the transcript file
            try:
                with open(transcript_file, "rb", encoding="utf-8") as f:
                    await update.message.reply_document(
                        document=f,
                        filename="Transcript.txt",
                        caption=f"📄 Your transcript for the video {youtube_data['Title']} is ready."
                    )

                logger.info(f" user_id={user.id} username={user.username} | Transcript sent to user.")
                
                # Send further options
                await update.message.reply_text("💡 What would you like to do next?", reply_markup=transcript_next_options_kb())
                return
            
            except Exception as e:
                logger.error(f"⚠️ Error during sending the transcript to user: \n{e}")

        else:
            logger.info(f" user_id={user.id} username={user.username} | Request exists but transcript doesn't exist")

    else:
        logger.info(f" user_id={user.id} username={user.username} | No previous request exists for given video id.")


    # Return response if caching not possible
    await update.message.reply_text(
        "⌛ Fetching the transcript now..."
    )

    # Send the transcript
    set_state(update, context, GENERATING_TRANSCRIPT)
    await send_transcript(update, context, video_id, youtube_data)

    return

"""---------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO SEND THE TRANSCRIPT
async def send_transcript(update:Update, context:ContextTypes.DEFAULT_TYPE, video_id, youtube_data):
    # Check state
    state = get_state(context)
    if state != GENERATING_TRANSCRIPT:
        logger.info(f" STATE | user_id={user.id} username={user.username} | Access from illegal state")
        await show_home(update, context)
        return   
    
    # Fetch the user
    user = update.effective_user

    # Choose the transcipt
    transcript = choose_transcript(video_id)

    # If no transcript redirect to transcript home
    if not transcript:
        logger.error(f" user_id={user.id} username={user.username} | No subtitles available for url provided by user.")
        await update.message.reply_text(
            f"⚠️ There are no transcripts available for the url that you provided. Please try a different url.", reply_markup = back_to_transcript_kb()
        )
        return
    
    # Get the transcript
    try:
        transcript_file = await get_transcript(transcript, user, video_id)
        logger.info(f" user_id={user.id} username={user.username} | Transcript generated successfuly for video id {video_id}")
    except Exception as e:
        logger.error(f" user_id={user.id} username={user.username} | Error while getting transcript.")
        await update.message.reply_text(
            f"⚠️ There was a problem while getting the transcript. Please try again.", reply_markup = back_to_transcript_kb()
        )
        return

    # Establish the session
    session = SessionLocal()

    # Create the new request object
    new_transcript_request = VideoRequests(user_id=user.id, video_id=video_id, transcript_path=transcript_file, completed=True)

    # Create new cache object
    new_cache = ReusableRequests(video_id=video_id, type="Transcript", file_path=transcript_file)
    
    # Save to db
    try:
        session.add(new_transcript_request)
        session.add(new_cache)
        session.commit()
        logger.info(f"  DB | user_id={user.id} username={user.username} | Transcript request saved to db.")
        
    except Exception as e:
        session.rollback()
        logger.error(f" DB | user_id={user.id} username={user.username} |Error while saving transcript request to db.")

    finally:
        session.close()    

    # Send the transcript file
    try:
        with open(transcript_file, "rb", encoding="utf-8") as f:
            await update.message.reply_document(
                document=f,
                filename="Transcript.txt",
                caption=f"📄 Your transcript for the video {youtube_data['Title']} is ready."
            )

        logger.info(f" user_id={user.id} username={user.username} | Transcript sent to user.")
        
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ There was a problem while sending the transcript. Please try again.", reply_markup = back_to_transcript_kb()
        )
        logger.error(f"⚠️ Error during sending the transcript to user: \n{e}")
        return


    # Send further options
    await update.message.reply_text("💡 What would you like to do next?", reply_markup=transcript_next_options_kb())
    return

"""---------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO FETCH THE TRANSCRIPT FOR NOTES PROCESS
async def fetch_transcript_for_notes(user, video_id):

    # GET DATA FROM DB IF ALREADY EXISTS
    #########################################################################

    # Check if a request exists for the same video id
    session = SessionLocal()
    prev_request = session.query(ReusableRequests).filter(
        (ReusableRequests.video_id == video_id) & 
        (ReusableRequests.type=="Transcript")
    ).first()
    
    # Check if the transcript file exists
    if prev_request:
        transcript_file = Path(prev_request.file_path)
        
        if transcript_file.exists():
            logger.info(f"user_id={user.id} username={user.username} | Transcript exists in db and in storage")
           
            # Send the transcript file
            try:
                with open(transcript_file, "rb", encoding="utf-8") as f:
                    transcript = f.read()

                logger.info(f"user_id={user.id} username={user.username} | Transcript extracted from db.")
                return transcript           
            
            except Exception as e:
                logger.error(f"⚠️ Error during extracting the transcript from db: \n{e}")

        else:
            logger.info(f"user_id={user.id} username={user.username} | Request exists but transcript doesn't exist")

    else:
        logger.info(f"user_id={user.id} username={user.username} | No previous request exists for given video id.")


    # OTHERWISE GENERATE A NEW TRANSCRIPT
    #########################################################################

    # choose a transcript option
    transcript_object = choose_transcript(video_id)

    # If no transcript return None
    if not transcript_object:
        logger.error(f"user_id={user.id} username={user.username} | No subtitles available for url provided by user.")
        transcript = None
        return transcript
    
    # Get the transcript if available
    try:
        transcript_file = await get_transcript(transcript_object, user, video_id)
        logger.info(f"user_id={user.id} username={user.username} | Transcript generated successfuly for video id {video_id}")
    except Exception as e:
        logger.error(f"user_id={user.id} username={user.username} | Error while getting transcript.")


    # SAVE TO DB
    #########################################################################

    # Create the new request object
    new_transcript_request = VideoRequests(user_id=user.id, video_id=video_id, transcript_path=transcript_file, completed=True)

    # Create new cache object
    new_cache = ReusableRequests(video_id=video_id, type="Transcript", file_path=transcript_file)
    
    # Save to db
    try:
        session.add(new_transcript_request)
        session.add(new_cache)
        session.commit()
        logger.info(f"DB | user_id={user.id} username={user.username} | Transcript request saved to db.")
        
    except Exception as e:
        session.rollback()
        logger.error(f"DB | user_id={user.id} username={user.username} |Error while saving transcript request to db.")

    finally:
        session.close()    

    # RETURN THE TRANSCRIPT
    #########################################################################
    with open(transcript_file, "rb", encoding="utf-8") as f:
        transcript = f.read()
        logger.info(f"user_id={user.id} username={user.username} | Transcript extracted from db.")
        return transcript 
    
"""---------------------------------------------------------------------------------------------------------------"""
# # REGISTER THE HANDLERS
# def register(app):
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, transcript_url_handler))
        