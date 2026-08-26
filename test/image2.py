import base64
from pathlib import Path
import requests
from ollama import chat


url = "https://res.cloudinary.com/dwcjokd3s/image/upload/v1783368889/LiveLink/uploads/xva7j9kelda8e1147snh.jpg"
img = Path(url).read_bytes()


# 3. Call the chat function with valid parameters
response = chat(
    model='gemma4:e2b',
    messages=[
        {
            'role': 'user',
            'content': 'What is in this file? Be concise.',
            'images': [img],  # Pass base64 string or raw bytes here
        }
    ],
)

print(response.message.content)