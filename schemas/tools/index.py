from pathlib import Path
from typing import Literal

from langchain.messages import ToolMessage
from langchain.tools import tool, ToolRuntime
import os
from core.config import settings
from langchain_protocol import Command
from ollama import chat


@tool("read_image")
def read_image(
    task: str,
    path: str,
    tool_runtime: ToolRuntime,
) -> str:
    """
    Read and analyze an image file from the user's computer.
    Use this when the user asks what is inside an image.
    """

    writer = tool_runtime.stream_writer

    image_path = Path(path)

    if not image_path.exists():
        return f"Image not found: {image_path}"

    if not image_path.is_file():
        return f"Path is not a file: {image_path}"

    try:
        img = image_path.read_bytes()

        writer({"message": f"Reading image: {image_path.name}"})

        response = chat(
            model="gemma4:e2b",
            messages=[
                {
                    "role": "user",
                    "content": task,
                    "images": [img],
                }
            ],
        )

        return response.message.content

    except Exception as e:
        return f"Failed to read image: {e}"


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

