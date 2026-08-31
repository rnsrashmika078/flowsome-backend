import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent


async def main():
    client = MultiServerMCPClient(
        {
            "math": {
                "transport": "stdio",  # Local subprocess communication
                "command": "python",
                # Absolute path to your math_server.py file
                "args": [r"C:\Users\Rashm\OneDrive\Desktop\hello.py"],
            },
        }
    )
    return client


if __name__ == "__main__":
    asyncio.run(main())
