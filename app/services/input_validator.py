# services
from app.services.youtube_data import *

# logger
from app.config.logging import logger

def validate_input(input, user):
    # Split the input into urls
    urls = [url.strip() for url in input.split("\n")]

    # Initialise the output dictionary
    valid_url_data = []
    invalid_urls = []

    for url in urls:
        # Get video id
        try:
            video_id = get_video_id(url)
            valid_url_data.append({"url":url, "video_id":video_id})  

        except Exception as e:
            logger.exception(f"user_id={user.id} username={user.username} | Invalid URL sent by user. Couldn't fetch video_id for {url} \n {e}")
            invalid_urls.append({"url":url})       

        finally:
            continue

    return valid_url_data, invalid_urls