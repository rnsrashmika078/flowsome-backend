from deepagents import SubAgentMiddleware
from deepagents.backends import StateBackend
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from schemas.models.lang.chatModels import local, simple_model
from schemas.services.middleware.customMiddlewares import (
    FlexibleFileSearchMiddleware,
    RecursiveGlobMiddleware,
    dynamic_model_middleware,
    generate_chat_title,
)
from deepagents.middleware.filesystem import FilesystemMiddleware
from langchain.agents.middleware import (
    ShellToolMiddleware,
    HostExecutionPolicy,
)
from langchain.agents.middleware import (
    SummarizationMiddleware,
)
from schemas.models.lang.chatModels import summarizeModel
import base64
from schemas.tools.graph import execute_python_task
from schemas.tools.index import internet_search, read_image
from schemas.tools.mcp.index import main
from schemas.tools.structured_output.so_output import extract_directory
import json


system_prompt = """
You are a helpful assistant.

For computer and filesystem tasks, use the available tools instead of guessing.

TOOLS:

1. execute_python_task
Use this tool for ANY computer-related task that can be performed with Python, including:
- Getting system information/configuration
- Finding files or folders
- Reading file contents
- Creating, editing, or deleting files
- Searching directories
- Checking installed software or packages
- Running commands/scripts
- Inspecting the user's computer
- Any other task involving the user's local computer

2. read_image
Use this tool to read or analyze an image.

IMAGE TASKS:
- If the image path is unknown, first use execute_python_task to find the image.
- Once the path is known, use read_image with the exact path.
- Never guess an image location or its contents.
- Base your answer on the actual tool results.

For computer tasks, prefer execute_python_task over explaining how the user could do it manually.
"""


# messy
def clean_object(obj):
    try:
        if isinstance(obj, BaseMessage):
            data = {
                "type": obj.type,
                "content": obj.content,
                "id": getattr(obj, "id", None),
                "additional_kwargs": getattr(obj, "additional_kwargs", {}),
                "response_metadata": getattr(obj, "response_metadata", {}),
                "usage_metadata": getattr(obj, "usage_metadata", {}),
            }
            if isinstance(obj, ToolMessage):
                if isinstance(obj.content, dict):
                    print("YES TOOL CALL CONTENT IS DICT")

                data["tool_call_id"] = obj.tool_call_id
                data["artifact"] = obj.artifact
            if isinstance(obj, AIMessage):
                data["tool_calls"] = obj.tool_calls
            return data

        elif hasattr(obj, "model_dump"):  # check for pydantic model or nt
            return obj.model_dump()

        elif isinstance(obj, dict):
            return {k: clean_object(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [clean_object(item) for item in obj]

        return obj
    except Exception as e:
        print(f"Error: {e}")


def _json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, dict):
        return all(_json_safe(k) and _json_safe(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return all(_json_safe(item) for item in value)
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


# new clean version
def clean_object_v2(obj):
    try:
        if hasattr(obj, "model_dump"):
            return clean_object_v2(obj.model_dump())
        elif isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                if k == "shell_session_resources":
                    continue
                cleaned = clean_object_v2(v)
                if _json_safe(cleaned):
                    result[k] = cleaned
            return result
        elif isinstance(obj, (list, tuple)):
            result = []
            for item in obj:
                cleaned = clean_object_v2(item)
                if _json_safe(cleaned):
                    result.append(cleaned)
            return result
        return obj
    except Exception as e:
        print(f"Error: {e}")


def ImageEncode(file_content, requests):
    if file_content:
        response_file = requests.get(file_content)
        image_bytes = response_file.content
        encoded_img = base64.b64encode(image_bytes).decode("utf-8")
        return encoded_img
    return None


async def init_create_agent(checkpointer):
    client = MultiServerMCPClient(
        {
            "math": {
                "transport": "stdio",
                "command": "python",
                "args": [
                    r"C:\Users\Rashm\OneDrive\Desktop\PROJECTS\REACT_NEXT_JS_PROJECTS\Flowsome\flowsome-backend\scripts\math-server.py"
                ],
            },
        }
    )
    mcp_tools = await client.get_tools()

    tools = mcp_tools + [internet_search, execute_python_task, read_image]
    agent = create_agent(
        model=local,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        middleware=[
            #             SubAgentMiddleware(
            #                 backend=StateBackend(),
            #                 subagents=[
            #                     {
            #                         "name": "image_reader",
            #                         "description": (
            #                             "Reads and analyzes image files from "
            #                             "the user's Windows computer."
            #                         ),
            #                         "system_prompt": """
            # You are an image-reading specialist.
            # When the user asks you to read or inspect an image
            # from their computer, use the read_image tool.
            # Do not guess image contents.
            # """,
            #                         "tools": [read_image],
            #                         "model": local,
            #                         "middleware": [],
            #                     }
            #                 ],
            #             ),
            # ShellToolMiddleware(
            #     workspace_root="C:/",
            #     shell_command=[r"C:\Program Files\Git\bin\bash.exe", "--norc"],
            #     execution_policy=HostExecutionPolicy(),
            # ),
            # dynamic_model_middleware,
            generate_chat_title,
            # RecursiveGlobMiddleware(),
            # pre-built middlewares
            SummarizationMiddleware(
                model=summarizeModel,
                trigger=("tokens", 4000),
                keep=("messages", 20),
            ),
            # FilesystemMiddleware(),
            # FlexibleFileSearchMiddleware(
            #     root_path="C:/",
            #     use_ripgrep=True,
            #     max_file_size_mb=10,
            # ),
        ],
    )

    return agent
