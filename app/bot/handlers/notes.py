# python
import asyncio

# telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

# handlers
from app.bot.handlers.home import show_home

# keyboards
from app.bot.keyboards.home_kb import nav_home_keyboard
from app.bot.keyboards.notes_kb import *
from app.bot.state_management import *

# callbacks
from app.bot.callbacks import *

# logging
from app.config.logging import logger

# services
from app.services.youtube_data import *
from app.services.transcriptor import *
from app.services.notes_processor import *
from app.services.input_validator import validate_input


# jobs
from app.bot.jobs.notes_job import notes_job

# db
from app.db.base import SessionLocal
from app.db.models import *

"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO ASK USER FOR URL
async def ask_notes_url(update:Update, context:ContextTypes.DEFAULT_TYPE):
    # 1) Establish the session
    session = SessionLocal()

    # 2) Check for last modes
    try:
        user_id = update.effective_user.id
        user = session.query(User).filter(User.id == user_id).first()
        current_mode = NotesModes.get_name_for_callback(session,user_id=user.id,callback_data=user.current_mode_callback)
        current_processing = user.current_processing
        output_type = NotesModes.get_output_for_callback(session,user_id=user.id,callback_data=user.current_mode_callback)

    except Exception as e:
        logger.exception(f" DB | Fatal error in fetching user\n{e}")

        error_text = (
            "⚠️ *Something went wrong while fetching the user.*\n\n"
            "Please try again in a moment."
            )
        
        await update.callback_query.message.edit_text(error_text, reply_markup=nav_home_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    finally:
        session.close()  

    # 3) Return notes menu and prompt for url
    await update.callback_query.message.edit_text(
        f"📝 -- NOTES MODE -- 📝\n\n⏳ Processing Mode:- {current_processing}\n⚙️ Notes Mode:- {current_mode} (Output = {output_type})\n\n🔗 Please send the YouTube link(s) you want notes of:",
        reply_markup= notes_main_kb()
    )

"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO RECEIVE THE URL
async def notes_url_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    # 0) VERIFY STATE
    ######################################################################
    state = get_state(context)
    user = update.effective_user

    if state != AWAITING_NOTES_URL:
        logger.info(f" STATE | user_id={user.id} username={user.username} | Access from illegal state")
        await show_home(update, context)
        return
    
    
    # 1) GET VALID URLS AND INVALID URLS
    ######################################################################
    input = update.message.text

    # Validate the input
    valid_url_data, invalid_urls = validate_input(input, user)

    
    # 2) FETCH THE PROCESSING MODE
    ######################################################################
    session = SessionLocal()

    try:
        user_id = update.effective_user.id
        user = session.query(User).filter(User.id == user_id).first()
        current_processing = user.current_processing

    except Exception as e:
        logger.exception(f" DB | Fatal error in fetching user\n{e}")

        error_text = (
            "⚠️ *Something went wrong while fetching the user.*\n\n"
            "Please try again in a moment."
            )
        
        await update.message.reply_text(error_text, reply_markup=nav_home_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    finally:
        session.close()

    
    # 3) GET THE NOTES DATA FOR VALID URLS
    ######################################################################

    set_state(update, context, GENERATING_NOTES)

    # Return response to update user
    await update.message.reply_text(
        "⌛ Generating notes now..."
    )

    # get the notes job results
    notes_job_results = await notes_job(user, valid_url_data, current_processing)
    logger.info(f"user_id={user.id} username={user.username} | Notes job results received as {notes_job_results}")


    
    # 4) SEND THE NOTES DATA AND THE INVALID URLS
    ######################################################################

    set_state(update, context, SENDING_NOTES)

    await send_notes(update, context, notes_job_results, invalid_urls)
    return

"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO SEND THE NOTES
async def send_notes(update, context, results, invalid_urls):
    logger.info("Entered send notes handler")
    logger.info(f"Results received as: \n{results}")
    session = SessionLocal()

    target = update.message or update.callback_query.message

    try:
        user = session.query(User).filter(User.id == update.effective_user.id).first()
        output_type = NotesModes.get_output_for_callback(session,user_id=user.id,callback_data=user.current_mode_callback)
        logger.info(f"Output type extracted as: {output_type}")


    except Exception as e:
        logger.exception(f"DB | Fatal error in fetching user\n{e}")
        await target.reply_text(
            "⚠️ Something went wrong while fetching user preferences.",
            reply_markup=nav_home_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    finally:
        session.close()

    # ------------------------------------------------------------------
    # 1) VERIFY STATE
    # ------------------------------------------------------------------

    state = get_state(context)

    if state != SENDING_NOTES:
        logger.info(f"STATE | user_id={user.id} username={user.username} | Access from illegal state")
        await show_home(update, context)
        return

    target = update.message or update.callback_query.message

    # ------------------------------------------------------------------
    # 2) SEND NOTES
    # ------------------------------------------------------------------
    from app.utils.text_splitter import split_text_for_telegram
    
    if output_type == "txt":
        logger.info(f"user_id={user.id} username={user.username} | Sending notes as text")

        for entry in results:
            logger.info(f"send_notes | processing video_id={entry.get('video_id')}")

            if entry.get("completed") is True:
                try:
                    with open(Path(entry["notes_path"]), "r", encoding="utf-8") as f:
                        notes = f.read()

                    # Chunking notes correctly
                    chunks = split_text_for_telegram(notes, max_length=4000) # Give extra margin for telegram limit
                    
                    # Ensure first chunk gets the title
                    if chunks:
                        chunks[0] = f"**{entry['title']}**\n\n{chunks[0]}"

                    for idx, chunk in enumerate(chunks):
                        try:
                            await target.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
                            await asyncio.sleep(0.3) # brief pause to prevent rate limit from multi-message blasts
                        except Exception as chunk_e:
                            logger.exception(f"send_notes | Error sending chunk {idx} for text notes\n{chunk_e}")
                            await target.reply_text(f"⚠️ Failed to send part of the notes for {entry['url']}.")
                            break # stop sending following chunks if one failed

                    logger.info(
                        f"user_id={user.id} username={user.username} | Notes sent for {entry['video_id']} in {len(chunks)} chunks"
                    )

                except Exception as e:
                    logger.exception(f"send_notes | Error sending notes\n{e}")
                    await target.reply_text(
                        f"⚠️ Failed to send notes for {entry['url']}"
                    )

            else:
                await target.reply_text(
                    f"⚠️ Could not generate notes for {entry['url']}.\nReason: {entry.get('reason')}",
                    reply_markup=back_to_notes_kb()
                )

    elif output_type == "pdf":
        logger.info(f"user_id={user.id} username={user.username} | PDF output selected")
        from app.services.file_converter import md_to_pdf

        for entry in results:
            logger.info(f"send_notes | processing pdf for video_id={entry.get('video_id')}")

            if entry.get("completed") is True:
                try:
                    # Convert to PDF
                    pdf_path = md_to_pdf(entry["notes_path"], user.id)
                    
                    final_output = f"**{entry['title']}**\n\n_Here are your notes exported as PDF!_"
                    
                    # Send document
                    with open(pdf_path, 'rb') as pdf_file:
                        await asyncio.wait_for(
                            target.reply_document(
                                document=pdf_file,
                                filename=f"{entry['title']}.pdf",
                                caption=final_output,
                                parse_mode=ParseMode.MARKDOWN
                            ),
                            timeout=30 # longer timeout for file upload
                        )

                    logger.info(
                        f"user_id={user.id} username={user.username} | PDF Notes sent for {entry['video_id']}"
                    )

                except Exception as e:
                    logger.exception(f"send_notes | Error sending pdf notes\n{e}")
                    await target.reply_text(
                        f"⚠️ Failed to send PDF notes for {entry['url']}"
                    )

            else:
                await target.reply_text(
                    f"⚠️ Could not generate notes for {entry['url']}.\nReason: {entry.get('reason')}",
                    reply_markup=back_to_notes_kb()
                )

    # ------------------------------------------------------------------
    # 4) WARN ABOUT INVALID URLS
    # ------------------------------------------------------------------
    if invalid_urls:
        invalid_text = "\n".join(invalid_urls)
        await target.reply_text(
            f"⚠️ Notes could not be generated for the following invalid URLs:\n{invalid_text}"
        )

    # ------------------------------------------------------------------
    # 5) FOLLOW-UP OPTIONS
    # ------------------------------------------------------------------
    await target.reply_text(
        "💡 What would you like to do next?",
        reply_markup=notes_next_options_kb()
    )
    logger.info(f"user_id={user.id} username={user.username} | Next options sent to user.")

    return


"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO PROVIDE OPTIONS FOR PROCESSING MODES
async def choose_processing_mode(update:Update, context:ContextTypes.DEFAULT_TYPE):
    # 0) Check state
    current_state = get_state(context)
    user = update.effective_user

    if current_state != CHOOSING_PROCESSING_MODE:
        logger.info(f" STATE | user_id={user.id} username={user.username} | Access from illegal state")
        set_state(update, context, AWAITING_NOTES_URL)
        await ask_notes_url(update, context)
        return

    # 1) Establish the session
    session = SessionLocal()

    # 2) Get current modes
    try: 
        user_id = update.effective_user.id
        user = session.query(User).filter(User.id == user_id).first()
        current_mode = NotesModes.get_name_for_callback(session,user_id=user.id,callback_data=user.current_mode_callback)
        current_processing = user.current_processing
        output_type = NotesModes.get_output_for_callback(session,user_id=user.id,callback_data=user.current_mode_callback)


    except Exception as e:
        logger.exception(f" DB | Fatal error in fetching user\n{e}")

        error_text = (
            "⚠️ *Something went wrong while fetching the user.*\n\n"
            "Please try again in a moment."
            )
        
        await update.callback_query.message.edit_text(error_text, reply_markup=nav_home_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    finally:
        session.close()

    # 3) Return processing mode menu
    await update.callback_query.message.edit_text(
        f"Please choose the type of processing you want:-", reply_markup=choose_processing_modes_kb(),parse_mode=ParseMode.MARKDOWN
    )

"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO SET THE PROCESSING MODE ONCE CHOSEN
async def set_processing_mode(update:Update, context:ContextTypes.DEFAULT_TYPE):
    # 0) Check state
    current_state = get_state(context)
    user = update.effective_user

    if current_state != CHOOSING_PROCESSING_MODE:
        logger.info(f" STATE | user_id={user.id} username={user.username} | Access from illegal state")
        set_state(update, context, AWAITING_NOTES_URL)
        await ask_notes_url(update, context)
        return

    # Choice made by user
    callback = update.callback_query
    await callback.answer()
    choice = callback.data

    # 1) Establish the session
    session = SessionLocal()

    # 2) Get user data
    user_id = update.effective_user.id
    user = session.query(User).filter(User.id == user_id).first()

    # 3) Get processing modes
    processing_modes = session.query(ProcessingModes).all()
    
    # 4) Create a mapping of each mode with its callback
    processing_mode_mapping = dict({})
    for mode in processing_modes:
        processing_mode_mapping[mode.callback_data] = mode.name

    # 5) Update the user data based on the choice
    user.current_processing = processing_mode_mapping[choice]

    try:
        session.add(user)
        session.commit()
        logger.info(f" MODE | user_id={user_id} username={user.username} | User has changed processing mode to {processing_mode_mapping[choice]}")
        user = session.query(User).filter(User.id == user_id).first()
    except Exception as e:
        session.rollback()
        logger.exception(f" DB | Fatal error during processing mode updation\n{e}")

        error_text = (
            "⚠️ *Something went wrong while updating the processing mode.*\n\n"
            "Please try again in a moment."
            )
        
        await update.callback_query.message.edit_text(error_text, reply_markup=nav_home_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    finally:
        session.close()
    
    # 6) Return the note mode choosing prompt
    set_state(update, context, CHOSSING_OUTPUT_TYPE)
    await choose_output_type(update, context)

"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO PROVIDE OPTIONS FOR OUTPUT TYPE
async def choose_output_type(update:Update, context:ContextTypes.DEFAULT_TYPE):
    # 0) Check state
    current_state = get_state(context)
    user = update.effective_user

    if current_state != CHOSSING_OUTPUT_TYPE:
        logger.info(f" STATE | user_id={user.id} username={user.username} | Access from illegal state")
        set_state(update, context, AWAITING_NOTES_URL)
        await ask_notes_url(update, context)
        return

    # # 1) Establish the session
    # session = SessionLocal()

    # # 2) Get current modes
    # try: 
    #     user_id = update.effective_user.id
    #     user = session.query(User).filter(User.id == user_id).first()
    #     current_mode = NotesModes.get_name_for_callback(session,user_id=user.id,callback_data=user.current_mode_callback)
    #     current_processing = user.current_processing
    #     current_output = user.current_output

    # except Exception as e:
    #     logger.exception(f" DB | Fatal error in fetching user\n{e}")

    #     error_text = (
    #         "⚠️ *Something went wrong while fetching the user.*\n\n"
    #         "Please try again in a moment."
    #         )
        
    #     await update.callback_query.message.edit_text(error_text, reply_markup=nav_home_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    # finally:
    #     session.close()

    # 3) Return processing mode menu
    await update.callback_query.message.edit_text(
        f"Please choose the output type you want:-", reply_markup=choose_output_type_kb(),parse_mode=ParseMode.MARKDOWN
    )

"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO SET THE OUTPUT TYPE ONCE CHOSEN
async def set_output_type(update:Update, context:ContextTypes.DEFAULT_TYPE):
    # 0) Check state
    current_state = get_state(context)
    user = update.effective_user

    if current_state != CHOSSING_OUTPUT_TYPE:
        logger.info(f" STATE | user_id={user.id} username={user.username} | Access from illegal state")
        set_state(update, context, AWAITING_NOTES_URL)
        await ask_notes_url(update, context)
        return

    # Choice made by user
    callback = update.callback_query
    await callback.answer()
    choice = callback.data

    # 1) Establish the session
    session = SessionLocal()

    # 2) Get user data
    user_id = update.effective_user.id
    user = session.query(User).filter(User.id == user_id).first()

    session.close()


    # 3) Update the user data based on the choice
    if choice == CB_NOTES_OUTPUT_TEXT:
        output_type = "txt"
    elif choice == CB_NOTES_OUTPUT_PDF:
        output_type = "pdf"

   

    
    # 4) Return the note mode choosing prompt
    set_state(update, context, CHOOSING_NOTES_MODE)
    await update.callback_query.message.edit_text(f"Please choose the note mode that you want:-", reply_markup=choose_notes_modes_kb(output_type, user.id),parse_mode=ParseMode.MARKDOWN)

"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# FUNCTION TO SET THE NOTES MODES
async def set_notes_mode(update:Update, context:ContextTypes.DEFAULT_TYPE):
    # 0) Check state
    current_state = get_state(context)
    user = update.effective_user
    
    if current_state != CHOOSING_NOTES_MODE:
        logger.info(f" STATE | user_id={user.id} username={user.username} | Access from illegal state")
        set_state(update, context, AWAITING_NOTES_URL)
        await ask_notes_url(update, context)
        return

    # Choice made by user
    callback = update.callback_query
    await callback.answer() 
    choice = callback.data

    # 1) Establish the session
    session = SessionLocal()

    # 2) Get modes
    user_id = update.effective_user.id
    user = session.query(User).filter(User.id == user_id).first()
    default_notes_modes = session.query(DefaultNotesModes).all()
    notes_modes = session.query(NotesModes).filter(NotesModes.user_id == user_id).all()

    # 3) Create mapping of all note modes
    notes_modes_mapping = dict({})

    for mode in default_notes_modes:
        notes_modes_mapping[mode.callback_data] = mode.name

    for mode in notes_modes:
        notes_modes_mapping[mode.callback_data] = mode.name

    # 4) Update the user data based on the choice
    user.current_mode_callback = choice

    try:
        session.add(user)
        session.commit()
        logger.info(f" MODE | user_id={user_id} username={user.username} | User has changed notes mode to {notes_modes_mapping[choice]}")
    except Exception as e:
        session.rollback()
        logger.exception(f" DB | Fatal error during processing mode updation\n{e}")

        error_text = (
            "⚠️ *Something went wrong while updating the notes mode.*\n\n"
            "Please try again in a moment."
            )
        
        await update.callback_query.message.edit_text(error_text, reply_markup=nav_home_keyboard(), parse_mode=ParseMode.MARKDOWN)
 
    # 5) Return to Notes main page
    set_state(update, context, AWAITING_NOTES_URL)
    await ask_notes_url(update, context)

"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# Register
def register(app):
    app.add_handler(CallbackQueryHandler(set_processing_mode, pattern=r"^pr_mode:"))
    app.add_handler(CallbackQueryHandler(set_output_type, pattern=r"^note_output:"))
    app.add_handler(CallbackQueryHandler(set_notes_mode, pattern=r"^note_mode:"))

