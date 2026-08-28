from pathlib import Path

from langchain.messages import ToolMessage
from langchain.tools import tool, ToolRuntime
import os

from langchain_protocol import Command


@tool("read_file")  # Custom name
def read_file_tool(path_to_file: str, file_name: str, toolRunTime: ToolRuntime) -> str:
    """read file from user computer.

    input:
        path_to_file: path to the file including file name -> ex: "desktop/abc.txt"
        fileName: file name -> ex: abc.txt

    """
    print(f"path_to_file : {path_to_file}")
    writer = toolRunTime.stream_writer
    writer({"message": f"Reading file {file_name}"})
    home_dir = os.path.expanduser("~")
    file_path = os.path.join(home_dir, path_to_file)
    print(f"file path: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
            # return f"Content: {content}"
    except FileNotFoundError:
        writer({"message": ""})
        return "File not found."

    except PermissionError:
        writer({"message": ""})
        return "Permission denied."

    except Exception as e:
        writer({"message": ""})
        return f"Error reading file: {e}"


@tool("read_image")  # Custom name
def read_image(image_path: str, user_prompt: str, toolRunTime: ToolRuntime) -> str:
    """read file from user computer.

    input:
        imagePath: path to the image
        user_prompt: user request that related to the image file

    """
    from ollama import chat

    writer = toolRunTime.stream_writer
    writer({"message": "Reading image"})
    # Pass in the path to the image
    # img = r"C:\Users\Rashm\OneDrive\Pictures\Screenshots\ss.png"
    # You can also pass in base64 encoded image data
    # img = base64.b64encode(Path(path).read_bytes()).decode()
    # or the raw bytes
    # img = Path(image_path).read_bytes()

    response = chat(
        model="gemma4:e2b",
        stream=False,
        think="low",
        messages=[
            {
                "role": "user",
                "content": "read this image",
                "images": [image_path],
            }
        ],
    )
    return Command(f"Content: {response.message.content}")
