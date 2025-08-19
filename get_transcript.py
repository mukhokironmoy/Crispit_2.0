from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re
from datetime import timedelta, datetime
import os
from log_handler import logger
from pathlib import Path


def get_video_id(url):
    # Handle different YouTube URL types
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    elif "youtube.com/live/" in url:
        return url.split("youtube.com/live/")[-1].split("?")[0]

    # Fallback regex
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)
    

    raise ValueError("Invalid YouTube URL format")


def format_time(seconds):
    """Convert seconds to hh:mm:ss format"""
    return str(timedelta(seconds=int(seconds)))

def get_language_options(video_id):
    ytt_api = YouTubeTranscriptApi()  # ✅ Must instantiate
    transcript_list = ytt_api.list(video_id)

    # Show options
    options_as_text = []
    options = []
    for i, transcript in enumerate(transcript_list):
        t_type = "Auto" if transcript.is_generated else "Manual"
        options.append(transcript)
        options_as_text.append(f"{transcript.language} - {t_type}")

    return options, options_as_text


def get_transcript(options, selected_idx, out_dir="telegram_out_data", user=None, chat=None):
    try:
        selected_transcript = options[selected_idx]

        # Fetch it
        transcript_data = selected_transcript.fetch()

        # Ensure folder exists
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        basename = None

        # Build a readable, unique filename
        # lang_code = getattr(selected_transcript, "language_code", None) or getattr(selected_transcript, "language", "xx")
        base = basename or f"{user.id}_transcript"
        file_path = out_path / f"{base}.txt"

        # write transcript to file
        with file_path.open('w', encoding='utf-8', newline="\n") as f:
            for entry in transcript_data:
                formatted_time = format_time(entry.start)  # ✅ Use dot notation
                text = entry.text                          # ✅ Use dot notation
                f.write(f"{formatted_time} : {text}\n")

        # return file path
        return str(file_path)

    except Exception as e:
        raise ValueError(f"Error occured : {e}")


if __name__ == "__main__":
    video_url = input("📥 Paste the YouTube video URL: ").strip()
    video_id = get_video_id(video_url)
    options, options_as_text = get_language_options(video_id)
    choice = int(input("Pick one: "))
    get_transcript(options, choice)



