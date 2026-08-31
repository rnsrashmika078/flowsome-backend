from pathlib import Path
from typing import Literal

from langchain.messages import ToolMessage
from langchain.tools import tool, ToolRuntime
import os
from core.config import settings
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


from tavily import TavilyClient

tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
