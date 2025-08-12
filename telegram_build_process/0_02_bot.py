import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()
BOT_TOKEN = os.getenv("telegram_token")

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("telegram_token is missing. Did you create .env and activate venv?")
    
    bot = Bot(token=BOT_TOKEN)
    me = await bot.get_me()  # <-- await the async method
    print("Bot has started... ✅")
    print("Bot username is:", me.username)

if __name__ == "__main__":
    asyncio.run(main())  # start the event loop and run main()
