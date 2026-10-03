from langchain.tools import tool
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy


class ExtractPath(BaseModel):
    """Extract the directory path mentioned by the user."""

    directory_path: str = Field(
        description="The directory path provided or mentioned by the user."
    )


@tool("extract_directory")
def extract_directory(query: str) -> str:
    """Extract the directory path mentioned by the user in the AI chat."""

    model = "gemma4:e2b"

    local = ChatOllama(
        model=model,
        reasoning=False,
    )

    agent = create_agent(
        model=local,
        tools=[],
        response_format=ToolStrategy(ExtractPath),
    )

    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    })

    return result["structured_response"].directory_path