import re

def get_str_from_food_dict(food_dict: dict):
    result = ", ".join([f"{item}: {qty}" for item, qty in food_dict.items()])
# BASICALLY THIS FUNCTION TAKES A DICTIONARY OF FOOD ITEMS AND QUANTITIES AND RETURNS A STRING WITH COMMA INBETWEEN THEM.
    return result

def extract_session_id(session_str: str):  
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)  # Changed to group(1) to get the session ID
        return extracted_string

    return ""