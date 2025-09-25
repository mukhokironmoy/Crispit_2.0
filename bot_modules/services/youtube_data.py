import json, urllib.parse, urllib.request

def get_yt_data(url: str) -> dict:
    o = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
    with urllib.request.urlopen(o, timeout=5) as r:
        data = json.loads(r.read().decode("utf-8"))
        clean_title = data.get("title", "").replace("\xa0", " ")
    return {
        "Title": clean_title,
        "Uploader": data.get("author_name"),
    }

if __name__ == "__main__":
    url = input("Enter the url: ")
    print(get_yt_data(url))