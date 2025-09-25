# Crispit Telegram Bot

## Setup

1.  Clone the repo

2.  Create a virtual environment:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # on Linux/Mac
    .venv\Scripts\activate      # on Windows
    ```

3.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4.  Create a `.env` file in the root with:

    ```
    telegram_token=YOUR_TELEGRAM_BOT_TOKEN
    GEMINI_API_KEY=YOUR_GEMINI_KEY
    ```

5.  Run the bot:

    ```bash
    python run.py
    ```

## Project Structure

- `bot_modules/core` → App setup, state, logging
- `bot_modules/handlers` → All bot command/callback handlers
- `bot_modules/keyboards` → Inline keyboard layouts
- `bot_modules/services` → External integrations (YouTube, transcripts, Gemini, PDF)
- `bot_modules/config` → Environment/config variables
