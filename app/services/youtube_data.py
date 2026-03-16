import json, urllib.parse, urllib.request
import re

def get_yt_data(url: str) -> dict:
    o = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
    with urllib.request.urlopen(o, timeout=5) as r:
        data = json.loads(r.read().decode("utf-8"))
        clean_title = data.get("title", "").replace("\xa0", " ")
    return {
        "Title": clean_title,
        "Uploader": data.get("author_name"),
    }

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

    raise ValueError("Invalid YouTube URL format!")

if __name__ == "__main__":
    url = input("Enter the url: ")
    
    print(get_yt_data(url))
    print(get_video_id(url))