import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.middleware import generate_chat_title
from agent.models import chat_model, summarize_model
from agent.prompt import SYSTEM_PROMPT
from tools.files import edit_file, list_files, read_file, write_file
from tools.image import read_image
from tools.python_task import execute_python_task
from tools.rag import rag_tool
from tools.search import internet_search

MATH_SERVER_PATH = Path(__file__).resolve().parent.parent / "scripts" / "math_server.py"


async def build_agent(checkpointer):
    client = MultiServerMCPClient(
        {
            "math": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(MATH_SERVER_PATH)],
            },
        }
    )
    mcp_tools = await client.get_tools()

    tools = mcp_tools + [
        internet_search,
        execute_python_task,
        read_image,
        read_file,
        write_file,
        edit_file,
        list_files,
        rag_tool,
    ]

    return create_agent(
        model=chat_model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        middleware=[
            generate_chat_title,
            SummarizationMiddleware(
                model=summarize_model,
                trigger=("tokens", 4000),
                keep=("messages", 20),
            ),
        ],
    )
