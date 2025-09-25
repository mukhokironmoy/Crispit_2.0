import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("telegram_token")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Default directories
DATA_DIR = "telegram_out_data"
INPUT_DIR = "telegram_in_data"
