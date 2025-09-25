from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ParseMode

from bot_modules.keyboards.navigation_kb import go_back

def build_help_text() -> str:
    return (
        "*Here’s what I can do (so far):*"
        "\n\n"
        "• `/start` — show the welcome screen with buttons\n\n"
        "   ◦ *Get Transcript* — Get the transcript of a YouTube video by providing a link.\n"
        "   ◦ *Get Notes* — Get notes for a YouTube video by providing a link\n\n"
        "• `/help` — show this help\n\n"
        "• `/echo <text>` — repeat back your message"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            build_help_text(),
            reply_markup=go_back(),
            parse_mode=ParseMode.MARKDOWN
        )

# for when help is triggered from a button (home menu)
async def help_panel(q):
    await q.message.edit_text(
        build_help_text(),
        reply_markup=go_back(),
        parse_mode=ParseMode.MARKDOWN
    )

def register(app):
    app.add_handler(CommandHandler("help", help_cmd))
