from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from pathlib import Path
import re
import asyncio
import hashlib

# services
from app.services.youtube_data import get_video_id

"""---------------------------------------------------------------------------------------------------------------"""
# API SETUP
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

"""---------------------------------------------------------------------------------------------------------------"""
# GET NOTES
async def get_notes(transcript:str, prompt:str, filename:str, title=None, url=None):

    # Initialise the header text for the prompt
    header = ""

    # Add data
    if title:
        header = header + f"Title = {title}\n"
    if url:
        header = header + f"url = {url}\n"

    # Set the prompt
    prompt = header + prompt

    # Set the data
    data = prompt + transcript

    # Get the response from llm
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[data],
        config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0))
    )
    
    # Saving the notes
    notes_dir = Path(f"data/notes")
    notes_dir.mkdir(parents=True, exist_ok=True)
    notes_path = Path(f"{notes_dir}/{filename}.txt")

    with open(notes_path, 'w', encoding='utf-8') as f:
        f.write(response.text)

    return str(notes_path)
"""---------------------------------------------------------------------------------------------------------------"""

async def main():
    transcript_path = Path(r"data\transcripts\-lp2Kt6RJkQ_transcript.txt")

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    prompt_path = Path(r"data\prompts\02_Crispit_Default_pdf.txt")

    with open(prompt_path, 'r', encoding="utf-8") as f:
        prompt = f.read()

    notes = await get_notes(transcript, prompt, "notes", "https://www.youtube.com/watch?v=wvH0jNZMzIM")
    print(notes)
    
if __name__ == "__main__":
    asyncio.run(main())





    
    

