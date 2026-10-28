from pathlib import Path

from langchain.tools import ToolRuntime, tool
from ollama import chat

from agent.models import CHAT_MODEL


@tool("read_image")
def read_image(task: str, path: str, tool_runtime: ToolRuntime) -> str:
    """Read and analyze an image file from the user's computer.

    Args:
        task: What to analyze or answer about the image.
        path: Image file path on the local machine.
    """
    writer = tool_runtime.stream_writer
    image_path = Path(path).expanduser()

    if not image_path.exists():
        return f"Image not found: {image_path}"
    if not image_path.is_file():
        return f"Path is not a file: {image_path}"

    try:
        image_bytes = image_path.read_bytes()
        writer({"message": f"Reading image: {image_path.name}"})

        response = chat(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": task,
                    "images": [image_bytes],
                }
            ],
        )

        return response.message.content or ""
    except Exception as exc:
        return f"Failed to read image: {exc}"
