from langchain.agents import create_agent
from langchain.agents.middleware import FilesystemFileSearchMiddleware
from langchain.messages import HumanMessage
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

model = "gemma4:e2b"
local = ChatOllama(
    model=model,
    reasoning=False,
)

agent = create_agent(
    model=local,
    tools=[],
    middleware=[
        FilesystemFileSearchMiddleware(
            root_path=r"C:\Users\Rashm\OneDrive\Desktop\path",
            use_ripgrep=True,
            max_file_size_mb=10,
        ),
    ],
)

# Agent can now use glob_search and grep_search tools
result = agent.invoke(
    {"messages": [HumanMessage("Find all Python files containing 'async def'")]}
)
data = None
print(f"result:{result['messages']}")
for msg in result["messages"]:
    if isinstance(msg, AIMessage):
        data = {
            "type": msg.type,
            "content": msg.content,
            "id": getattr(msg, "id", None),
            "additional_kwargs": getattr(msg, "additional_kwargs", {}),
            "response_metadata": getattr(msg, "response_metadata", {}),
            "usage_metadata": getattr(msg, "usage_metadata", {}),
        }
        print(f"CONTENT: {msg.content}")

# print(data["content"])
# The agent will use:
# 1. glob_search(pattern="**/*.py") to find Python files
# 2. grep_search(pattern="async def", include="*.py") to find async functions
