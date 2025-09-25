import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters

from bot_modules.core.logging import logger
from bot_modules.core.state import (
    get_state, set_state, clear_state,
    STATE_MAKING_TRANSCRIPT, STATE_MAKING_NOTES
)
from bot_modules.services.transcript import get_transcript, get_video_id, get_language_options, safe_filename
from bot_modules.services.youtube_data import get_yt_data
from bot_modules.services.gemini_notes import get_notes
from bot_modules.services.file_converter import md_to_pdf
from bot_modules.keyboards.navigation_kb import CB_NAV_HOME
from bot_modules.keyboards.notes_kb import build_post_notes_keyboard

# ---- callback constants ----
CB_HOME_TRANSCRIPT = "home:transcript"

# ---- transcript route ----
async def get_transcript_options(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    user = update.effective_user
    chat = update.effective_chat

    # Parse video_id
    try:
        video_id = await asyncio.to_thread(get_video_id, url)
        logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Video id extracted: {video_id}")
    except Exception:
        logger.error(f"⚠️ ERROR | user_id={user.id} | chat_id={chat.id} | Invalid YouTube URL")
        await update.message.reply_text("⚠️ That doesn’t look like a valid YouTube link. Please send a proper URL.")
        return

    # Get available transcript options
    try:
        options, labels = await asyncio.to_thread(get_language_options, video_id)
        logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Transcript options extracted.")
    except Exception:
        logger.error(f"⚠️ ERROR | user_id={user.id} | chat_id={chat.id} | Error fetching transcript options")
        await update.message.reply_text("⚠️ I couldn’t fetch transcript options for that video.")
        clear_state(context)
        from bot_modules.handlers.home import show_home
        await show_home(update, context)
        return

    if not options:
        logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | No transcripts available")
        await update.message.reply_text("⚠️ No transcripts are available for this video.")
        clear_state(context)
        from bot_modules.handlers.home import show_home
        await show_home(update, context)
        return

    # Cache options for the selection step
    context.chat_data["tr_video_id"] = video_id
    context.chat_data["tr_options"] = options
    context.chat_data["tr_option_labels"] = labels

    # Offer choices
    await update.message.reply_text(
        "🔎 Choose which transcript to use:",
        reply_markup=build_transcript_options_keyboard(labels)
    )


def build_transcript_options_keyboard(labels: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(label, callback_data=f"tr:pick:{i}")] for i, label in enumerate(labels)]
    rows.append([InlineKeyboardButton("⬅️ Go back", callback_data=CB_NAV_HOME)])
    return InlineKeyboardMarkup(rows)


async def on_transcript_options_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    await q.answer()

    data = q.data
    if not data.startswith("tr:pick:"):
        return

    try:
        idx = int(data.split(":")[-1])
    except ValueError:
        await q.answer("Invalid option.", show_alert=True)
        return

    options = context.chat_data.get("tr_options", [])
    labels = context.chat_data.get("tr_option_labels", [])
    video_url = context.chat_data.get("last_transcript_url")

    if not options or idx < 0 or idx >= len(options):
        await q.answer("That option is no longer available.", show_alert=True)
        logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Invalid transcript option")
        return

    chosen_label = labels[idx]
    context.chat_data["tr_choice_idx"] = idx
    logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Chose transcript option: {chosen_label}")

    # Work in background
    await q.message.edit_text(f"✅ Selected transcript: {chosen_label}.\n⏳ Working on your transcript…")
    asyncio.create_task(process_transcript_job(video_url, context, q, options, idx, user, chat))


JOB_SEMAPHORE = asyncio.Semaphore(4)


async def process_transcript_job(video_url, context, q, options, idx, user, chat):
    async with JOB_SEMAPHORE:
        try:
            yt_data = get_yt_data(video_url)
            title = yt_data["Title"]

            file_path = await asyncio.to_thread(get_transcript, title, options, idx, user=user, chat=chat)
            context.chat_data["last_transcript_file"] = file_path
            logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Transcript saved at {file_path}")

            state = get_state(context)

            if state == STATE_MAKING_TRANSCRIPT:
                try:
                    with open(file_path, "rb") as f:
                        await q.message.reply_document(
                            document=f,
                            filename="Transcript.txt",
                            caption="📄 Your transcript is ready."
                        )
                    logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Transcript sent")
                except Exception:
                    logger.error("⚠️ ERROR sending transcript file", exc_info=True)
                    await q.message.reply_text("⚠️ I generated the file but couldn’t send it.")

                await q.message.reply_text("What next?", reply_markup=build_post_transcript_keyboard())

            elif state == STATE_MAKING_NOTES:
                await q.message.edit_text("⏳ Transcript extracted. Now generating your notes...")
                logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Transcript extracted, generating notes")

                title = safe_filename(title)
                try:
                    notes_file = await asyncio.to_thread(
                        get_notes, context.chat_data["last_transcript_url"], context.chat_data["notes_prompt_path"], file_path, None
                    )
                    logger.info(f"DEBUG | user_id={user.id} | chat_id={chat.id} | Notes generated")
                except Exception:
                    logger.error("Notes generation failed", exc_info=True)
                    await q.message.reply_text("❌ Sorry, I couldn’t generate notes.")
                    return

                notes_file = md_to_pdf(notes_file)

                try:
                    with open(notes_file, "rb") as f:
                        await q.message.reply_document(
                            document=f,
                            filename="Notes.pdf",
                            caption="📝 Your notes are ready!"
                        )
                except Exception:
                    logger.error("⚠️ ERROR sending notes file", exc_info=True)
                    await q.message.reply_text("⚠️ Generated notes but couldn’t send file.", reply_markup=build_post_notes_keyboard())

                clear_state(context)
                await q.message.reply_text("What next?", reply_markup=build_post_notes_keyboard())

        except Exception:
            logger.error("⚠️ Transcript job failed", exc_info=True)
            await q.message.reply_text("❌ Sorry, transcript failed.")


def build_post_transcript_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Home", callback_data=CB_NAV_HOME)]])


# ---- show transcript prompt (called from home) ----
async def show_transcript_prompt(q, context):
    set_state(context, "AWAITING_TRANSCRIPT_URL")
    await q.message.edit_text(
        "📜 Please send the YouTube link you want transcribed:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Go back", callback_data=CB_NAV_HOME)]])
    )


# ---- register handlers ----
def register(app):
    app.add_handler(CallbackQueryHandler(on_transcript_options_buttons, pattern=r"^tr:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, None))  # actual text handling in notes handler
