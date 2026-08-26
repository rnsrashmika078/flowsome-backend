import base64
import requests
from ollama import chat

url = "https://res.cloudinary.com/dwcjokd3s/image/upload/v1783368889/LiveLink/uploads/xva7j9kelda8e1147snh.jpg"
response_file = requests.get(url)
image_bytes = response_file.content

encoded_img = base64.b64encode(image_bytes).decode("utf-8")
# 3. Call the chat function with valid parameters
response = chat(
    model="gemma4:e2b",
    messages=[
        {
            "role": "user",
            "content": "What is in this file? Be concise.",
            "images": [encoded_img],  # Pass base64 string or raw bytes here
        }
    ],
)

print(response.message.content)
