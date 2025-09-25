from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def echo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        text = " ".join(context.args)
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("Usage: /echo <text>")

def register(app):
    app.add_handler(CommandHandler("echo", echo_cmd))
