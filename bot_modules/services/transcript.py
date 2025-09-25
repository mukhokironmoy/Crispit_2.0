from youtube_transcript_api import YouTubeTranscriptApi
import re
from datetime import timedelta
from pathlib import Path
from bot_modules.core.logging import logger
from bot_modules.services.youtube_data import get_yt_data


def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def get_video_id(url):
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    elif "youtube.com/live/" in url:
        return url.split("youtube.com/live/")[-1].split("?")[0]

    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)

    raise ValueError("Invalid YouTube URL format")


def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))


def get_language_options(video_id):
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)

    options = []
    options_as_text = []
    for transcript in transcript_list:
        t_type = "Auto" if transcript.is_generated else "Manual"
        options.append(transcript)
        options_as_text.append(f"{transcript.language} - {t_type}")

    return options, options_as_text


def get_transcript(title, options, selected_idx, out_dir="telegram_out_data", user=None, chat=None):
    try:
        selected_transcript = options[selected_idx]
        transcript_data = selected_transcript.fetch()

        if user:
            out_path = Path(out_dir) / str(user.id)
        else:
            out_path = Path(out_dir) / "test_run"
        out_path.mkdir(parents=True, exist_ok=True)

        title = safe_filename(title)

        if not user:
            base = "test_transcript"
        else:
            base = f"transcript_{title}"

        file_path = out_path / f"{base}.txt"

        with file_path.open('w', encoding='utf-8', newline="\n") as f:
            for entry in transcript_data:
                formatted_time = format_time(entry.start)
                text = entry.text
                f.write(f"{formatted_time} : {text}\n")

        return str(file_path)

    except Exception as e:
        raise ValueError(f"Error occured : {e}")


if __name__ == "__main__":
    video_url = input("📥 Paste the YouTube video URL: ").strip()
    yt_data = get_yt_data(video_url)
    title = yt_data["Title"]
    video_id = get_video_id(video_url)
    options, options_as_text = get_language_options(video_id)

    print("\nAvailable transcripts:")
    for i, label in enumerate(options_as_text):
        print(f"{i}: {label}")

    choice = int(input("Pick one: "))
    get_transcript(title, options, choice)
