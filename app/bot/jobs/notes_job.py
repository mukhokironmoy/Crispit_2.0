# processors
from app.services.notes_processor import *

# services
from app.services.input_validator import validate_input

async def notes_job(user:User, valid_url_data:list, current_processing:str):

    # If there is atleast one valid url then generate notes
    if len(valid_url_data)>0:

        # Route the input data to their respective processors and return the final output

        if current_processing == "Single":
            # Get result
            process_results = [await single_processor(user, valid_url_data[0])]
            logger.info(f"user_id={user.id} username={user.username} | Process result received as {process_results}")
            
            return process_results

        elif current_processing == "Batch (Default)":
            pass
        
        elif current_processing == "Batch (One per page)":
            pass
    
    # Otherwise return an empty list
    else:
        process_results = []