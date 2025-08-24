import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from log_handler import logger
from get_transcript import get_transcript, get_video_id, get_language_options
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import TelegramError
import asyncio

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# LOADING TOKEN
load_dotenv()
BOT_TOKEN = os.getenv("telegram_token")

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# LOGGER FUNCTIONS

# Logs only normal messages (no commands)
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

# Logs only commands
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

# Logs all button presses
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
# STATE MANAGEMENT

# ---- tiny state map ----
STATE_NONE                 = "NONE"
STATE_AWAIT_TRANSCRIPT_URL = "AWAITING_TRANSCRIPT_URL"
STATE_AWAIT_NOTES_URL      = "AWAITING_NOTES_URL"

def set_state(context: ContextTypes.DEFAULT_TYPE, value: str):
    context.chat_data["state"] = value

def get_state(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.chat_data.get("state", STATE_NONE)

def clear_state(context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["state"] = STATE_NONE

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# HOME ROUTE

# ---- callbacks (namespaced) ----
CB_HOME_TRANSCRIPT = "home:transcript"
CB_HOME_NOTES      = "home:notes"
CB_HOME_HELP       = "home:help"
CB_NAV_HOME        = "nav:home"

# building the welcome keyboard
def build_welcome_keyboard() -> InlineKeyboardMarkup:
    keyboard_layout = [
        [InlineKeyboardButton("Get Transcript", callback_data= CB_HOME_TRANSCRIPT)],
        [InlineKeyboardButton("Get Notes", callback_data=CB_HOME_NOTES)],
        [InlineKeyboardButton("Help", callback_data=CB_HOME_HELP)]

    ]
    return InlineKeyboardMarkup(keyboard_layout)

# setting the home text
def build_home_text() -> str:
    return "🏠 *Crispit Bot — Home*\nWhat would you like to do today?"

# defining home
async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(context)
    user = update.effective_user          # always safe: best-guess sender
    chat = update.effective_chat          # where it was sent
    msg  = update.effective_message       # the message object (can be None in some update types)

    welcome_text = f"*Hello {user.username}! Welcome to Crispit!*\n\n" + build_home_text()
    markup = build_welcome_keyboard()


    # If this came from /start or /menu (a message), send a new panel.
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN) 

    # If this came from a button tap (a callback), edit the existing panel (updates the menu in place)
    elif update.callback_query:
        q = update.callback_query
        await q.answer()
        await q.message.edit_text(welcome_text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN) 

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# BUTTON FUNCTIONS FOR BUTTONS FOR HOME ROUTE

# return home button
def go_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Go back", callback_data = CB_NAV_HOME)]])

# response for transcript button
async def show_transcript_prompt(q, context):
    set_state(context, STATE_AWAIT_TRANSCRIPT_URL)  # q is a CallbackQuery; PTB lets you pass it as context in our helper
    await q.message.edit_text(
        "📜 Please send the YouTube link you want transcribed: ",
        reply_markup = go_back()
    )

# response for notes button
async def show_notes_prompt(q, context):
    set_state(context, STATE_AWAIT_NOTES_URL)
    await q.message.edit_text(
        "📝 Please send the YouTube link you want summarized into notes: ",
        reply_markup = go_back()
    )

# diplay for help button
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
# BUTTON HANDLERS FOR BUTTONS FOR HOME ROUTE

# handler for home page
async def on_home_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query

    await q.answer()
    data = q.data  

    # Route based on callback_data
    if data == CB_HOME_TRANSCRIPT:
        await show_transcript_prompt(q, context)

    elif data == CB_HOME_NOTES:
        await show_notes_prompt(q, context)

    elif data == CB_HOME_HELP:
        await help_panel(q)

    else:
        await q.message.reply_text("🤔 I didn’t recognize that action.")

# handler for go back
async def go_back_buttons(update:Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query

    await q.answer()

    if q.data == CB_NAV_HOME:
        await show_home(update, context)

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# TRANSCRIPT ROUTE

# create keyboard for transcript options
def build_transcript_options_keyboard(labels: list[str]) -> InlineKeyboardMarkup:
    rows = []

    for i, label in enumerate(labels):
        rows.append([InlineKeyboardButton(label, callback_data=f"tr:pick:{i}")])
    
    rows.append([InlineKeyboardButton("⬅️ Go back", callback_data = CB_NAV_HOME)])

    return InlineKeyboardMarkup(rows)

# create keyboard for post transcript options
def build_post_transcript_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Make notes from this transcript", callback_data="notes:from_tr")],
        [InlineKeyboardButton("⬅️ Home", callback_data=CB_NAV_HOME)]
    ])

JOB_SEMAPHORE = asyncio.Semaphore(4)  # max 4 heavy jobs at once

async def process_transcript_job(context, q, options, idx, user, chat):
    async with JOB_SEMAPHORE:
        try:
            file_path = await asyncio.to_thread(get_transcript, options, idx, user=user, chat=chat)
            context.chat_data["last_transcript_file"] = file_path
            logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Transcript saved at: {file_path}")


            try:
                with open(file_path, "rb") as f:
                    await q.message.reply_document(
                        document = f,
                        filename = "Transcript.txt",
                        caption = "📄 Your transcript is ready."
                    )

            except Exception as e:
                logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | Sending transcript file failed", exc_info=e)
                await q.message.reply_text("⚠️ I generated the file but couldn’t send it.")

            # offer next steps
            await q.message.reply_text(
                "What next?",
                reply_markup=build_post_transcript_keyboard()
            )

        except Exception as e:
            logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | Transcript job failed", exc_info=e)
            await q.message.reply_text("❌ Sorry, transcript failed.")


# handler for transcript options
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

    if not options or idx<0 or idx>=len(options):
        await q.answer("That option is no longer available.", show_alert=True)  # show popup if you press a wrong option
        logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Invalid option chosen by user")
        return
    
    # store the chosen label
    chosen_label = labels[idx]
    context.chat_data["tr_choice_idx"] = idx
    logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User chose transcript option : {chosen_label}")


    # # give status update response
    # await q.message.edit_text(f"✅ Selected transcript: {chosen_label}.\n⏳ Generating transcript file...")

    # generate transcript and get output file path
    try:
        # give status update response
        await q.message.edit_text(f"✅ Selected transcript: {chosen_label}.\n⏳ Working on your transcript, this may take a few seconds…")
        
        # let the heavy work run in background
        asyncio.create_task(process_transcript_job(context, q, options, idx, user, chat))

    except Exception as e:
        logger.error(f"⚠️ ERROR | user_id={user.id} username={user.username} | chat_id={chat.id} | Transcript generation failed | \n\n", exc_info=e)
        await q.message.edit_text(
            "❌ Sorry, I couldn’t generate the transcript.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Home", callback_data=CB_NAV_HOME)]])
        )
        return
    
    # # send the output file as a document
    # try:
    #     with open(file_path, "rb") as f:
    #         await q.message.reply_document(
    #             document = f,
    #             filename = "Transcript.txt",
    #             caption = "📄 Your transcript is ready."
    #         )

    # except Exception as e:
    #     logger.error("Sending transcript file failed", exc_info=e)
    #     await q.message.reply_text("⚠️ I generated the file but couldn’t send it.")

    # # offer next steps
    # await q.message.reply_text(
    #     "What next?",
    #     reply_markup=build_post_transcript_keyboard()
    # )

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# NOTES ROUTE

# sample handler for notes button
async def on_notes_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "notes:from_tr":
        file_path = context.chat_data.get("last_transcript_file")
        if not file_path:
            await q.answer("No transcript file found in this chat.", show_alert=True)
            return

        await q.message.edit_text(
            "🧠 Notes generation will use the transcript you just received. (Coming up next!)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Home", callback_data=CB_NAV_HOME)]])
        )

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------"""
# COMMANDS

# help handler function
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


# echo handler function
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


# Receiving text handler
async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    # Only called for plain text (not commands) because of the filter we’ll add
    if update.message and update.message.text:
        text = update.message.text.strip()
        state = get_state(context)

        # AWAITING TRANSCRIPT LINK
        if state == STATE_AWAIT_TRANSCRIPT_URL: 

            logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | User in Transcript Route")

            url = text

            logger.info(f"DEBUG | user_id={user.id} username={user.username} | chat_id={chat.id} | Received url from user : {url}")

            # Placeholder: store somewhere if you like
            context.chat_data["last_transcript_url"] = url

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

            # We can clear the text-waiting state; selection now happens via buttons
            clear_state(context)
            return

        # AWAITING NOTES LINK
        if state == STATE_AWAIT_NOTES_URL:            
            url = text

            # Placeholder: store somewhere if you like
            context.chat_data["last_notes_url"] = url

            # Confirm 
            await update.message.reply_text(f"✅ Got the link for notes : {url}")
            clear_state(context)
            await show_home(update, context)
            return
        
        # Default echo behaviour
        await update.message.reply_text(f"Here's what you said : {text}")          


# photo handler functions
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
#ERROR HANDLING

# error handler function
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
# MAIN FUNCTION
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



    # error handlers
    app.add_error_handler(error_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))


    logger.info("✅ Bot is running (long polling). Press Ctrl+C to stop.")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
