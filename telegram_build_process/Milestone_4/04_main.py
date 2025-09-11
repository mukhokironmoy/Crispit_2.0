import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pathlib import Path
from log_handler import logger
from get_transcript import get_transcript, get_video_id, get_language_options, safe_filename
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import TelegramError
from youtube_data import get_yt_data
from gemini_notes import get_notes
from file_converter import md_to_pdf
import asyncio

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 1) LOADING TOKEN
load_dotenv()
BOT_TOKEN = os.getenv("telegram_token")

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 2) LOGGER FUNCTIONS

# 2.1) Function that logs only normal messages (no commands)
async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        u = update.effective_user
        c = update.effective_chat
        m = update.effective_message
        textish = m.text if m.text else m.caption if m.caption else None

        logger.info(
            "MSG | user_id=%s username=%s | chat_id=%s | text=%r",
            u.id if u else None,
            u.username if u else None,
            c.id if c else None,
            textish
        )

# 2.2) Function that logs only commands
async def log_all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        u = update.effective_user
        c = update.effective_chat
        m = update.effective_message
        logger.info(
            "CMD | user_id=%s username=%s | chat_id=%s | command=%r",
            u.id if u else None,
            u.username if u else None,
            c.id if c else None,
            m.text
        )

# 2.3) Function that logs all button presses
async def log_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        q = update.callback_query
        u = update.effective_user
        c = update.effective_chat
        logger.info(
            "CBQ | user_id=%s username=%s | chat_id=%s | data=%r",
            u.id if u else None,
            u.username if u else None,
            c.id if c else None,
            q.data
        )

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# ---- callbacks (namespaced) ----
CB_HOME_TRANSCRIPT = "home:transcript"
CB_HOME_NOTES      = "home:notes"
CB_HOME_HELP       = "home:help"
CB_NAV_HOME        = "nav:home"
CB_MAKE_NOTES = "notes:make_notes" 
CB_CHOOSE_NOTES_MODE = "notes:choose_notes_mode"
CB_BACK_TO_NOTES_MODES = "nav:back_to_notes_modes"

# ---- tiny state map ----
STATE_NONE                 = "NONE"
STATE_AWAIT_TRANSCRIPT_URL = "AWAITING_TRANSCRIPT_URL"
STATE_AWAIT_NOTES_URL      = "AWAITING_NOTES_URL"
STATE_CHOOSE_NOTES_MODE = "CHOOSE_NOTES_MODE"

# Transcript flow
STATE_AWAIT_TRANSCRIPT_URL = "AWAITING_TRANSCRIPT_URL"
STATE_MAKING_TRANSCRIPT    = "MAKING_TRANSCRIPT"

# Notes flow
STATE_AWAIT_NOTES_URL      = "AWAITING_NOTES_URL"
STATE_MAKING_NOTES         = "MAKING_NOTES"

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 3) STATE MANAGEMENT

def set_state(context: ContextTypes.DEFAULT_TYPE, value: str):
    context.chat_data["state"] = value

def get_state(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.chat_data.get("state", STATE_NONE)

def clear_state(context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["state"] = STATE_NONE

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 4) HOME ROUTE

# 4.1) building the welcome keyboard
def build_welcome_keyboard() -> InlineKeyboardMarkup:
    keyboard_layout = [
        [InlineKeyboardButton("Get Transcript", callback_data= CB_HOME_TRANSCRIPT)],
        [InlineKeyboardButton("Get Notes", callback_data=CB_HOME_NOTES)],
        [InlineKeyboardButton("Help", callback_data=CB_HOME_HELP)]

    ]
    return InlineKeyboardMarkup(keyboard_layout)

# 4.2) setting the home text
def build_home_text() -> str:
    return "🏠 *Crispit Bot — Home*\nWhat would you like to do today?"

# 4.3) defining home
async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(context)

    # defaults
    context.chat_data.setdefault("notes_mode", "Crispit Default")
    context.chat_data.setdefault("notes_prompt_path", Path(r"telegram_in_data\crispit_default_prompt.txt"))
    context.chat_data.setdefault("available_modes", [
        {
            "name": "Crispit Default",
            "path": Path(r"telegram_in_data\crispit_default_prompt.txt"),
            "built_in": True
        },
        {
            "name": "LLM Default",
            "path": Path(r"telegram_in_data\LLM_default_prompt.txt"),
            "built_in": True
        }
    ]
    )

    # load chat details
    user = update.effective_user          # always safe: best-guess sender
    chat = update.effective_chat          # where it was sent
    msg  = update.effective_message       # the message object (can be None in some update types)

    # create welcome text and button keyboard
    welcome_text = f"*Hello {user.username}! Welcome to Crispit!*\n\n" + build_home_text()
    markup = build_welcome_keyboard()

    # Handle how the start command operates

    # If called from /start or /menu (a message), send a new panel.
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN) 

    # If called from a button tap (a callback), edit the existing panel (updates the menu in place)
    elif update.callback_query:
        q = update.callback_query
        await q.answer()
        await q.message.edit_text(welcome_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN) 

# 4.4) handler for home page
async def on_home_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = update.effective_user
    chat = update.effective_chat

    await q.answer()
    data = q.data  

    # Route based on callback_data
    if data == CB_HOME_TRANSCRIPT:
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User in Transcript Route. Awaiting url....")
        await show_transcript_prompt(q, context)


    elif data == CB_HOME_NOTES:
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User in Notes Route. Awaiting url....")
        await show_notes_prompt(q, context)


    elif data == CB_HOME_HELP:
        await help_panel(q)

    else:
        await q.message.reply_text("🤔 I didn’t recognize that action.")

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# handler for go back
async def go_back_buttons(update:Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query

    await q.answer()

    if q.data == CB_NAV_HOME:
        await show_home(update, context)

    elif q.data == CB_BACK_TO_NOTES_MODES:
        await show_notes_modes(q, context)

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 5) HOME ROUTE BUTTONS

# 5.1) return home button
def go_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Go back", callback_data = CB_NAV_HOME)]])

# 5.2) response for transcript button
async def show_transcript_prompt(q, context):
    set_state(context, STATE_AWAIT_TRANSCRIPT_URL)  # q is a CallbackQuery; PTB lets you pass it as context in our helper
    
    await q.message.edit_text(
        "📜 Please send the YouTube link you want transcribed: ",
        reply_markup = go_back()
    )

# 5.3) response for notes button
async def show_notes_prompt(q, context):
    clear_state(context)
    set_state(context, STATE_AWAIT_NOTES_URL)  # q is a CallbackQuery; PTB lets you pass it as context in our helper
    
    await q.message.edit_text(
        f"[CURRENT MODE: {context.chat_data['notes_mode'].upper()}]\n\n📜 Please send the YouTube link you want to make notes of: ",
        reply_markup = build_notes_prompt_keyboard()
    )

# 5.4) keyboard for notes prompt
def build_notes_prompt_keyboard() -> InlineKeyboardMarkup:
    rows = []

    rows.append([InlineKeyboardButton("📝 Choose mode", callback_data = CB_CHOOSE_NOTES_MODE)])
    rows.append([InlineKeyboardButton("⬅️ Go back", callback_data = CB_NAV_HOME)])

    return InlineKeyboardMarkup(rows)

# 5.5) handler for notes prompt keyboard
async def on_notes_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = update.effective_user
    chat = update.effective_chat

    await q.answer()
    data = q.data 

    # Route based on callback_data
    if data == CB_CHOOSE_NOTES_MODE:
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User is choosing notes mode.")
        await show_notes_modes(q, context)

    elif data == CB_NAV_HOME:
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User has returned to start.")
        await show_home(update, context)

    elif q.data == CB_MAKE_NOTES:
        await show_notes_prompt(q, context)


# 5.4) response for help button
async def help_panel(q):
    text = (
        "*Here’s what I can do (so far):*"
        "\n\n"

        "• `/start` — show the welcome screen with the following buttons\n\n"
        "   ◦ *Get Transcript* — Get the transcript of a YouTube video by providing a link.\n"
        "   ◦ *Get Notes* — Get notes for a YouTube video by providing a link"
        "\n\n"

        "• `/help` — show this help\n\n"
    )
    await q.message.edit_text(text, reply_markup=go_back(), parse_mode = ParseMode.MARKDOWN)

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 6) TRANSCRIPT ROUTE

# 6.0) function for getting transcript options
async def get_transcript_options(update: Update, context: ContextTypes.DEFAULT_TYPE, url):
    user = update.effective_user
    chat = update.effective_chat

    # Parse video_id
    try:
        video_id = await asyncio.to_thread(get_video_id,url)
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Video id extracted : {video_id}")

    except Exception as e:
        logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | User sent invalid Youtube URL")
        await update.message.reply_text("⚠️ That doesn’t look like a valid YouTube link. Please send a proper URL.")
        return
    
    # Get available transcript options
    try:
        options, labels = await asyncio.to_thread(get_language_options,video_id)
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Transcript options extracted.")

    except Exception as e:
        logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | Error in fetching transcript options for URL.")
        await update.message.reply_text("⚠️ I couldn’t fetch transcript options for that video.")
        clear_state(context)
        await show_home(update, context)
        return
    
    if not options:
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | No transcripts available for provided url.")
        await update.message.reply_text("⚠️ No transcripts are available for this video.")
        clear_state(context)
        await show_home(update, context)
        return
    
    # Cache options for the selection step
    context.chat_data["tr_video_id"] = video_id
    context.chat_data["tr_options"] = options
    context.chat_data["tr_option_labels"] = labels

    # Offer choices as inline buttons
    await update.message.reply_text(
        "🔎 Choose which transcript to use:",
        reply_markup=build_transcript_options_keyboard(labels)
    )
    

# 6.1) create keyboard for transcript options
def build_transcript_options_keyboard(labels: list[str]) -> InlineKeyboardMarkup:
    rows = []

    for i, label in enumerate(labels):
        rows.append([InlineKeyboardButton(label, callback_data=f"tr:pick:{i}")])
    
    rows.append([InlineKeyboardButton("⬅️ Go back", callback_data = CB_NAV_HOME)])

    return InlineKeyboardMarkup(rows)

# 6.2) handler for transcript options
async def on_transcript_options_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = update.effective_user
    chat = update.effective_chat

    await q.answer()

    data = q.data

    # check if the button callback is for transcript option picking
    if data.startswith("tr:pick:"):
        try:
            idx = int(data.split(":")[-1]) # find the index of the chosen label
        except ValueError:
            await q.answer("Invalid option.", show_alert=True) # show popup if you press a wrong option
            return

    # get the options from context 
    options = context.chat_data.get("tr_options", [])
    labels = context.chat_data.get("tr_option_labels", [])
    video_url = context.chat_data.get("last_transcript_url")

    if not options or idx<0 or idx>=len(options):
        await q.answer("That option is no longer available.", show_alert=True)  # show popup if you press a wrong option
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Invalid option chosen by user")
        return
    
    # store the chosen label
    chosen_label = labels[idx]
    context.chat_data["tr_choice_idx"] = idx
    logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User chose transcript option : {chosen_label}")


   # generate transcript and get output file path
    try:
        # give status update response
        await q.message.edit_text(f"✅ Selected transcript: {chosen_label}.\n⏳ Working on your transcript, this may take a few seconds…")
        
        # let the heavy work run in background
        asyncio.create_task(process_transcript_job(video_url, context, q, options, idx, user, chat))

    except Exception as e:
        logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | Transcript generation failed | \n\n", exc_info=e)
        await q.message.edit_text(
            "❌ Sorry, I couldn’t generate the transcript.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Home", callback_data=CB_NAV_HOME)]])
        )
        return

# 6.3) create a job semaphore for multi users
JOB_SEMAPHORE = asyncio.Semaphore(4)  # max 4 heavy jobs at once

# 6.4) Process the transcript
async def process_transcript_job(video_url, context, q, options, idx, user, chat):
    async with JOB_SEMAPHORE:
        try:
            # get the video title 
            yt_data = get_yt_data(video_url)
            title = yt_data["Title"]

            # generate the transcript
            file_path = await asyncio.to_thread(get_transcript, title, options, idx, user=user, chat=chat)
            context.chat_data["last_transcript_file"] = file_path
            logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Transcript saved at: {file_path}")

            state = get_state(context)
            
            if state == STATE_MAKING_TRANSCRIPT:
                try:
                    with open(file_path, "rb") as f:
                        await q.message.reply_document(
                            document = f,
                            filename = "Transcript.txt",
                            caption = "📄 Your transcript is ready."
                        )
                    
                    logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Transcript sent.")


                except Exception as e:
                    logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | Sending transcript file failed", exc_info=e)
                    await q.message.reply_text("⚠️ I generated the file but couldn’t send it.")

                
                # offer next steps
                await q.message.reply_text(
                    "What next?",
                    reply_markup=build_post_transcript_keyboard()
                )

            elif state == STATE_MAKING_NOTES:

                # don’t send transcript, directly call notes generator
                await q.message.edit_text(
                    "⏳ Transcript extracted. Now generating your notes..."
                )
                logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Transcript extracted successfully. Generating notes now..")

                title = safe_filename(title)

                try:
                    notes_file = await asyncio.to_thread(
                        get_notes, context.chat_data["last_transcript_url"], context.chat_data["notes_prompt_path"], file_path, None
                    )

                    logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Notes generated successfully. Sending file now..")

                except Exception as e:
                    logger.error("Notes generation failed", exc_info=e)
                    await q.message.reply_text("❌ Sorry, I couldn’t generate notes.")

                notes_file = md_to_pdf(notes_file)

                try:
                    with open(notes_file, "rb") as f:
                        await q.message.reply_document(
                            document=f,
                            filename="Notes.pdf",
                            caption="📝 Your notes are ready!"
                        )
                        
                except Exception as e:
                    logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | Sending notes file failed", exc_info=e)
                    await q.message.reply_text("⚠️ I generated the notes file but couldn’t send it.", reply_markup= build_post_notes_keyboard())

                
                logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Notes sent successfully.")

                clear_state(context)

                await q.message.reply_text("What next?", reply_markup = build_post_notes_keyboard())



        except Exception as e:
            logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | Transcript job failed", exc_info=e)
            await q.message.reply_text("❌ Sorry, transcript failed.")
    
# 6.5) create keyboard for post transcript options
def build_post_transcript_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Home", callback_data=CB_NAV_HOME)]
    ])
"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 7) NOTES ROUTE

# 7.0) get available modes
async def get_notes_modes(update: Update, context:ContextTypes.DEFAULT_TYPE):
    # check if this chat has available modes or assigns defaults
    context.chat_data.setdefault("available_modes", [
        {
            "name": "Crispit Default",
            "path": Path(r"telegram_in_data\crispit_default_prompt.txt"),
            "built_in": True
        },
        {
            "name": "LLM Default",
            "path": Path(r"telegram_in_data\LLM_default_prompt.txt"),
            "built_in": True
        }
    ]
    )


# 7.1) response for notes modes button
async def show_notes_modes(q, context):
    set_state(context, STATE_CHOOSE_NOTES_MODE)
    await q.message.edit_text(
        f"[CURRENT MODE: {context.chat_data['notes_mode'].upper()}]\n\n📝 Please choose the mode of notes:",
        reply_markup=build_notes_modes_keyboard(context)
    )


# 7.2) build_notes_modes_keyboard
def build_notes_modes_keyboard(context) -> InlineKeyboardMarkup:
    rows = []
    modes = context.chat_data["available_modes"]

    for i, mode in enumerate(modes):
        rows.append([InlineKeyboardButton(f"📒 {mode['name']}", callback_data=f"mode:pick:{i}")])

    rows.append([InlineKeyboardButton("------", callback_data="mode:blank")])
    rows.append([InlineKeyboardButton("➕ Add Custom Mode", callback_data="mode:add")])
    rows.append([InlineKeyboardButton("⬅️ Go back", callback_data=CB_HOME_NOTES)])
    return InlineKeyboardMarkup(rows)

# 7.3) handler for notes modes
async def on_notes_modes_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = update.effective_user
    chat = update.effective_chat

    await q.answer()

    data = q.data

    # check if the button callback is for notes mode picking
    if data.startswith("mode:pick:"):
        try:
            idx = int(data.split(":")[-1]) # find the index of the chosen label
        except ValueError:
            await q.answer("Invalid option.", show_alert=True) # show popup if you press a wrong option
            return

        modes = context.chat_data["available_modes"]

        if not modes or idx<0 or idx>=len(modes):
            await q.answer("That option is no longer available.", show_alert=True)  # show popup if you press a wrong option
            logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Invalid option chosen by user")
            return
        
        # store the chosen mode
        chosen_mode = modes[idx]
        context.chat_data["notes_mode"] = chosen_mode["name"]  # store name
        context.chat_data["notes_prompt_path"] = chosen_mode["path"]  # store path
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User chose mode : {chosen_mode}")

    
        clear_state(context)

        await show_notes_prompt(q, context)

    elif data == "mode:add":
        await q.message.edit_text("➕ Feature not implemented yet. Here you’ll be able to add a custom mode.")

def build_post_notes_keyboard() -> InlineKeyboardMarkup:
    rows = []

    rows.append([InlineKeyboardButton("📜 Get notes for another video", callback_data=CB_HOME_NOTES)])
    rows.append([InlineKeyboardButton("⬅️ Back to Home", callback_data=CB_NAV_HOME)])
    return InlineKeyboardMarkup(rows)



# 7.3) function for getting notes

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 8) COMMANDS

# 8.1) help handler function
def build_help_text() -> str:
    return (
        "*Here’s what I can do (so far):*"
        "\n\n"

        "• `/start` — show the welcome screen with the following buttons\n\n"
        "   ◦ *Get Transcript* — Get the transcript of a YouTube video by providing a link.\n"
        "   ◦ *Get Notes* — Get notes for a YouTube video by providing a link"
        "\n\n"

        "• `/help` — show this help\n\n"
    )

# 8.2) help command function
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user          # always safe: best-guess sender
    chat = update.effective_chat          # where it was sent
    msg  = update.effective_message       # the message object (can be None in some update types)

    if msg:
        await msg.reply_text(
            build_help_text(),
            reply_markup=go_back(),
            parse_mode=ParseMode.MARKDOWN
        )


# 8.3) echo handler function
async def echo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    # If user typed: /echo hello world
    if context.args:
        text = " ".join(context.args)
        await update.message.reply_text(text)

    else:
        await update.message.reply_text("Usage: /echo <text>")


# 8.4) Receiving text handler
async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    state = get_state(context)

    # ---- Case 1: Transcript URL ----
    if state == STATE_AWAIT_TRANSCRIPT_URL:
        url = text
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Received url from user : {url}")

        # Placeholder: store somewhere if you like
        context.chat_data["last_transcript_url"] = url

        clear_state(context)
        set_state(context, STATE_MAKING_TRANSCRIPT)
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Generating Transcript now...")

        await get_transcript_options(update, context, url)
        return

    # ---- Case 2: Notes URL ----
    elif state == STATE_AWAIT_NOTES_URL:
        url = text
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Received url from user : {url}")

        # Placeholder: store somewhere if you like
        context.chat_data["last_transcript_url"] = url
        
        clear_state(context)
        set_state(context, STATE_MAKING_NOTES)
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Generating Notes now...")

        # but first → run the SAME transcript route
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Fetching Transcript...")
        await get_transcript_options(update, context, url)
        return
    
    else :
        await update.message.reply_text(f"Here's what you said : {text}")     
   


# 8.5) photo handler functions
async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    photos = msg.photo  # list[PhotoSize], smallest → largest

    if not photos:
        return  # safety

    largest = photos[-1]  # best quality
    caption = msg.caption or "(no caption)"

    info = (
        "📸 Got your photo!\n"
        f"- Size: {largest.width}×{largest.height}\n"
        f"- File ID ends with: …{str(largest.file_id)[-6:]}\n"
        f"- Caption: {caption}"
    )
    await msg.reply_text(info)

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 9) ERROR HANDLING

# 9.1) error handler function
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    """Log the error and send a message to yourself if needed."""
    logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | Exception while handling an update:", exc_info=context.error)

    # You can also notify the user something went wrong
    if update and hasattr(update, "effective_message") and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Oops! Something went wrong on my end. The developer’s been notified."
        )

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# 10) MAIN FUNCTION
def main():
    if not BOT_TOKEN:
        raise RuntimeError("telegram_token is missing. Check .env and that your venv is active.")

    app = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()

    # log handlers
    app.add_handler(MessageHandler(filters.COMMAND, log_all_commands), group=-1)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, log_all_messages), group=-1)
    app.add_handler(CallbackQueryHandler(log_all_callbacks), group=-1)

    # command handlers
    app.add_handler(CommandHandler("start", show_home))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("echo", echo_cmd))

    # button handlers
    app.add_handler(CallbackQueryHandler(on_home_buttons, pattern=r"^home:"))
    app.add_handler(CallbackQueryHandler(go_back_buttons, pattern=r"^nav:"))
    app.add_handler(CallbackQueryHandler(on_transcript_options_buttons, pattern=r"^tr:"))
    app.add_handler(CallbackQueryHandler(on_notes_buttons, pattern=r"^notes:"))
    app.add_handler(CallbackQueryHandler(on_notes_modes_buttons, pattern=r"^mode:"))

    # error handlers
    app.add_error_handler(error_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))

    logger.info("✅ Bot is running (long polling). Press Ctrl+C to stop.")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
