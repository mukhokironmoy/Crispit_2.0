# Crispit Project - Requirements Specification

## 1. Introduction
Crispit is a Telegram Bot and accompanying application designed to fetch YouTube video transcripts, process them using Large Language Models (LLMs), and generate concise, structured notes or summaries for users. The system supports single and batch processing of videos, customizable prompts for notes generation, and multiple output formats.

## 2. Functional Requirements

### 2.1 User Interaction & Bot Navigation
* **FR 1.1 Command Handling:** The bot must respond to standard Telegram commands (e.g., `/start`, `/help`) and provide an interactive Home Menu.
* **FR 1.2 Inline Keyboards:** The system must use interactive inline keyboards for navigation, selecting notes modes, and managing batch processing.
* **FR 1.3 Error Handling:** The bot must graciously catch user input errors (e.g. invalid YouTube URLs) and provide clear, actionable feedback to the user. 
* **FR 1.4 State Management:** The bot must maintain user state tracking across interactive operations (e.g., navigating menus, waiting for batch uploads).

### 2.2 Video & Transcript Processing
* **FR 2.1 YouTube Extraction:** The system must parse YouTube URLs and interface with YouTube services to retrieve auto-generated or manual video transcripts.
* **FR 2.2 Text Splitting & Limitations:** Transcripts exceeding specific length thresholds must be split intelligently into chunks or limited to avoid LLM token starvation and context overflow.

### 2.3 Notes Generation & LLM Integration
* **FR 3.1 LLM Processing:** The system must pass chunks of transcripts to an LLM service along with predefined or user-defined prompts to generate structured notes.
* **FR 3.2 Notes Modes:** Users must be able to create, edit, and delete custom "Notes Modes". A Notes Mode contains a specific prompt (e.g., "Summarize in bullet points") and an expected output format (PDF or TXT).
* **FR 3.3 Default Modes:** The system must provide out-of-the-box Default Notes Modes that cannot be modified by the user.

### 2.4 File Output & Delivery
* **FR 4.1 Output Formats:** The system must support generating final notes in multiple formats, specifically `TXT` and `PDF`.
* **FR 4.2 Single vs Batch Processing:**
  * **Single Mode:** Process one YouTube video at a time and return its notes.
  * **Batch Mode:** Accept multiple URLs and process them sequentially, delivering a single combined output file or individual files per video based on the user's batch preference.

### 2.5 Caching & Reusability
* **FR 5.1 Request Caching:** The system must store previously processed transcripts and generated notes for generic prompts. 
* **FR 5.2 Reusable Outputs:** If a user requests a video that has already been processed with the exact same mode/prompt, the bot must immediately return the cached file instead of calling the LLM API again.

### 2.6 Data Storage & User Management
* **FR 6.1 Database Tracking:** The system must store user profiles, custom modes, video processing history, and recurring requests in a relational database (via SQLAlchemy).
* **FR 6.2 Local File Storage:** The system must persist generated assets locally (Text/PDF files, raw transcripts) prior to sending them back over the Telegram API.

---

## 3. Non-Functional Requirements (NFRs)

### 3.1 Performance & Efficiency
* **NFR 1.1 Response Time:** The bot should confirm receipt of a YouTube link within 2 seconds. The overall processing time will depend on the LLM API latency, but the bot must send asynchronous status updates (e.g., "Processing transcript...") to prevent timeouts.
* **NFR 1.2 API Optimization:** The system must heavily prioritize the `ReusableRequests` cache to minimize tokens sent to the LLM API and reduce operating costs.

### 3.2 Reliability & Fault Tolerance
* **NFR 2.1 API Resilience:** Network failures with the YouTube extraction service or LLM provider must not crash the bot. The bot must retry or alert the user gracefully.
* **NFR 2.2 Token Limits:** The system must safeguard against overflowing the LLM token limits by implementing strict algorithmic text splitting (`text_limit.py`).

### 3.3 Security & Privacy
* **NFR 3.1 Input Validation:** All external inputs, specially YouTube URLs, must be sanitized to prevent injection attacks or unexpected service behavior.
* **NFR 3.2 Data Isolation:** Custom user prompts and user history must be strictly mapped to the specific Telegram user ID to prevent data leakage between users.

### 3.4 Maintainability
* **NFR 4.1 Module Separation:** The architecture must enforce a clear separation between routing/handlers, core logic (services), and data layers (db).
* **NFR 4.2 Logging:** The system must implement comprehensive logging (`config/logging.py`) for all LLM errors, bot timeouts, and general request tracking for debugging purposes.

### 3.5 Scalability
* **NFR 5.1 Async Architecture:** The application must utilize an asynchronous architecture (typical of `aiogram` or similar asynchronous Telegram bot frameworks) to ensure that slow LLM or YouTube transcript inferences do not block the event loop for other concurrent users.
