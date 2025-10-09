import re
import random

def get_response(user_input, chat_history):
    return random.choice([
        "Let me look into that for you.",
        "Here's what I found based on your issue.",
        "That seems like a common mechanical problem. Here's an insight..."
    ])

def generate_title_from_message(message):
    return message.strip()[:40]

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)
