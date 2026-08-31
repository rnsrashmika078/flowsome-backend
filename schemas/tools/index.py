from pathlib import Path

from langchain.messages import ToolMessage
from langchain.tools import tool, ToolRuntime
import os

from langchain_protocol import Command
from ollama import chat


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


# @tool("generate_chat_title")
# def generate_chat_title(firstMessage: str, toolRunTime: ToolRuntime) -> str:
#     """generate title for chat at beginning only ( at first message of chat).

#     input:
#         firstMessage:string -> user first message
#     """
#     response = chat(
#         model="qwen2.5-coder:3b",
#         messages=[
#             {
#                 "role": "user",
#                 "content": f"generate title for the chat based on below message. no preamble:   first Message: {firstMessage}",
#             }
#         ],
#     )

#     print(response.message.content)

#     writer = toolRunTime.stream_writer
#     writer({"message": "Generating title to the chat"})

#     return {"title": response.messages.content}
