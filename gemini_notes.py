from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from pathlib import Path
from get_transcript import get_transcript, get_language_options, get_video_id
from youtube_data import get_yt_data

import re

def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)


# API Setup
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Get file paths
DEFAULT_PROMPT = Path(r"telegram_in_data\crispit_default_prompt.txt")
DEFAULT_TRANSCRIPT = Path(r"telegram_out_data\test_run\test_transcript.txt")
DEFAULT_NOTES = Path(r"telegram_out_data\test_notes.txt")


def get_notes(video_url, prompt_path=DEFAULT_PROMPT, transcript_path=DEFAULT_TRANSCRIPT, notes_path=None):
    prompt_path = Path(prompt_path)
    transcript_path = Path(transcript_path)

    yt_data = get_yt_data(video_url)
    title = safe_filename(yt_data["Title"])

    if notes_path is None:
        out_dir = transcript_path.parent
        notes_path = out_dir / f"notes_{title}.md"
        # notes_path = out_dir / f"notes_{title}.md"
    else:
        notes_path = Path(notes_path)

    prompt_first_line = f"Title = Test Notes \nVideo Title = {yt_data['Title']} \nUrl = {video_url}\n\n"

    sample_file = client.files.upload(file=transcript_path)

    with open(prompt_path, 'r', encoding="utf8") as f:
        prompt = f.read()

    prompt = prompt_first_line + prompt

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[sample_file, prompt],
        config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0))
    )

    with open(notes_path, 'w', encoding='utf8') as f:
        f.write(response.text)

    return notes_path



if __name__ == "__main__":
    # Get transcript
    video_url = input("📥 Paste the YouTube video URL: ").strip()
    video_id = get_video_id(video_url)
    options, options_as_text = get_language_options(video_id)



    # print("\nAvailable transcripts:")
    # for i, label in enumerate(options_as_text):
    #     print(f"{i}: {label}")   # show index and label

    # choice = int(input("Pick one: "))
    # get_transcript(options, choice)

    get_notes(video_url)