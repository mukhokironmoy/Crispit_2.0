from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re
from datetime import timedelta
import os


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


def transcript(url):
    try:
        video_id = get_video_id(url)
        print(f"[DEBUG] Extracted Video ID: {video_id}")

        ytt_api = YouTubeTranscriptApi()  # ✅ Must instantiate
        transcript_list = ytt_api.list(video_id)

        # Try manually created transcript first
        try:
            transcript_obj = transcript_list.find_manually_created_transcript(['en'])
            print("[INFO] Using manually created English transcript.")
        except:
            # Fall back to auto-generated
            transcript_obj = transcript_list.find_generated_transcript(['en'])
            print("[INFO] Using auto-generated English transcript.")

        transcript_data = transcript_obj.fetch()

        # Make sure 'data' directory exists
        os.makedirs("data", exist_ok=True)

        with open("data/transcript.txt", 'w', encoding='utf-8') as f:
            for entry in transcript_data:
                formatted_time = format_time(entry.start)  # ✅ Use dot notation
                text = entry.text                          # ✅ Use dot notation
                f.write(f"{formatted_time} : {text}\n")


        print("✅ Transcript saved to data/transcript.txt")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    video_url = input("📥 Paste the YouTube video URL: ").strip()
    transcript(video_url)
