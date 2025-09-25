from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters

# ---- photo handler ----
async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    photos = msg.photo  # list[PhotoSize]

    if not photos:
        return

    largest = photos[-1]
    caption = msg.caption or "(no caption)"

    info = (
        "📸 Got your photo!\n"
        f"- Size: {largest.width}×{largest.height}\n"
        f"- File ID ends with: …{str(largest.file_id)[-6:]}\n"
        f"- Caption: {caption}"
    )
    await msg.reply_text(info)

def register(app):
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
