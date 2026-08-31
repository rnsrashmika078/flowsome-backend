from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from schemas.models.lang.chatModels import local
from schemas.services.middleware.customMiddlewares import (
    dynamic_model_middleware,
    generate_chat_title,
)
from langchain.agents.middleware import (
    FilesystemFileSearchMiddleware,
    SummarizationMiddleware,
)
from schemas.models.lang.chatModels import summarizeModel
import base64
from schemas.tools.mcp.index import main


system_prompt = """
    You are a helpful assistant!. 

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


# new clean version
def clean_object_v2(obj):
    try:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()

        elif isinstance(obj, dict):
            return {k: clean_object_v2(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [clean_object_v2(item) for item in obj]

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


async def init_create_agent(checkpointer, root_path):
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
    tools = await client.get_tools()
    agent = create_agent(
        model=local,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        middleware=[
            # dynamic_model_middleware,
            generate_chat_title,
            # pre-built middlewares
            SummarizationMiddleware(
                model=summarizeModel,
                trigger=("tokens", 4000),
                keep=("messages", 20),
            ),
            FilesystemFileSearchMiddleware(
                root_path=root_path,
                # root_path=root_path,
                use_ripgrep=True,
                max_file_size_mb=10,
            ),
        ],
    )

    return agent
