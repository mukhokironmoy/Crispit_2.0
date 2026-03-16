# Crispit Project Implementation Overview

This document provides a comprehensive summary of the current state of implementation for the **Crispit** Telegram Bot (Version 2.2). It outlines the underlying architecture, how individual components interact, and the existing system capabilities.

---

## 1. System Architecture

The Crispit bot is designed using a modular architecture with clear separation of concerns. It is built using Python, leveraging the `python-telegram-bot` wrapper for Telegram API interactions, `SQLAlchemy` for relational database management, and Google's `genai` SDK for Large Language Model capabilities.

The primary modules of the architecture are:
- **Bot Layer (Handlers & Keyboards)**: Interfaces directly with the user on Telegram.
- **Service Layer**: Handles external API integrations and core business logic (YouTube, Gemini, PDF generation).
- **Database Layer**: Manages persistent state, caching, settings, and user preferences.
- **Configuration & Utilities**: Centralized application settings, logging, and helpers.

---

## 2. Core Components and Interaction Flow

### A. Bot Layer (`app/bot/`)
- **`app.py` & `router.py`**: The entry point initializes the Telegram Bot `Application` and sets up global loggers to track messages, callbacks, and commands. `router.py` acts as a central switchboard, determining which handler executes based on callback data buttons or user text input states.
- **State Management (`state_management.py`)**: Stores user-specific states in memory via `context.chat_data` (e.g., waiting for notes URL, choosing processing mode) to ensure the bot context is isolated per user session.
- **Handlers (`home.py`, `notes.py`, `transcript.py`)**: 
  - `home.py`: Registers new users into the DB and displays the main menu.
  - `notes.py`: Orchestrates the main workflow—taking a YouTube URL, triggering the generator job, and returning text chunks or PDF documents to the user. It also dynamically queries the database for user-chosen output formats, processing types, and prompts.
- **Keyboards**: Generates dynamic `InlineKeyboardMarkup` objects for users to easily navigate their preferences (e.g., choosing "Single" vs "Batch" processing, "txt" vs "pdf" outputs, or varying LLM prompt strategies).

### B. Service Layer (`app/services/`)
This is the core execution engine of the application where data is fetched and transformed.
- **`youtube_data.py` & `transcriptor.py`**: Extracts the video ID from user URLs and utilizes `youtube-transcript-api` to pull subtitles (preferring manual English over auto-generated). Transcripts are cached locally to `data/transcripts/`.
- **`gemini_notes.py`**: Initializes the `google-genai` client (using `gemini-2.5-flash`). It wraps user transcript data along with custom instruction prompts (fetched from the database) to generate concise bulleted summaries.
- **`notes_processor.py`**: The integrator service for a standard YouTube-to-Notes job. It fetches the transcript via `transcriptor`, fetches the chosen user prompt from the database, feeds it into `gemini_notes`, creates a DB tracking record (`VideoRequests`, `ReusableRequests`), and returns the final file path to the handler.
- **`file_converter.py`**: Converts markdown text output into a styled PDF document using the `markdown-pdf` library.

### C. Database Layer (`app/db/`)
SQLAlchemy powers the SQLite/PostgreSQL layer via `models.py`. Key models include:
- **`User`**: Tracks Telegram user IDs, usernames, and their active default configurations (current mode callback, processing style).
- **`NotesModes` & `DefaultNotesModes`**: Holds prompt configurations. It distinguishes between global default prompts (e.g., "Crisp bulleted summary") and user-customized prompts.
- **`ProcessingModes`**: Allows the app to scale towards processing either Single videos or Batch playlists.
- **`VideoRequests` & `ReusableRequests`**: Implements a caching mechanism. If a video has been requested previously, the transcript and notes paths are stored persistently so they can be reused without wasting LLM tokens or API bandwidth.

### D. Utilities (`app/utils/`)
- **`text_splitter.py`**: Ensures the Telegram bot text limit (4096 characters per message) is respected by chunking long responses smoothly without breaking words.

---

## 3. Current System Capabilities

Based on the implemented source code, the system currently supports:

1. **User Registration & State Tracking**: Users seamlessly interact with the bot; their preferences and navigation states are tracked securely.
2. **Dynamic Configuration Options**:
   - **Processing Modes**: Users can select how URLs are handled (Single vs. Batch).
   - **Output Preferences**: The bot dynamically provides output as either a direct multi-message text in Telegram or a packaged, downloadable `.pdf` file.
   - **Customizable Prompts**: Users can select different prompt presets to target how the LLM summarizes the context.
3. **Automated Transcript Extraction**: Robust failovers that capture the most accurate YouTube subtitles available (fallback to auto-generated if manual isn't present).
4. **Data Caching & Reusability**: The system saves both raw transcripts and final notes locally (`data/transcripts/` & `data/notes/`), linked via the database. It prevents repeated identical API calls for the same video.
5. **Generative Processing**: Fully implemented integration with the Gemini 2.5 Flash model, capable of understanding large context logic mapping prompts over video transcripts.
6. **Graceful Error Handling**: Fallbacks and localized user warnings exist for unavailable transcripts, processing failures, and Telegram API transmission errors.

---

## 4. Next Steps & Missing Elements
- While the architecture holds hooks for "**Batch Processing**" models and handling multi-URL playlists, complete iteration implementations for parsing playlists are currently stubbed in `ProcessingModes` mapping but depend on future handler integrations.
- Further expansion of PDF stylings and specific text formatting constraints, which lie inside the `file_converter.py` logic.
