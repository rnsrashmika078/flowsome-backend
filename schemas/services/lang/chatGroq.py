from langchain_groq import ChatGroq
from core.config import settings
from langchain.agents import create_agent

# from langgraph.checkpoint.postgres import PostgresSaver
from core.config import settings
from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from ..middleware.customMiddlewares import welcome_back_message

llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.chat_model,
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
)


async def get_agent():
    async with AsyncPostgresSaver.from_conn_string(
        settings.DATABASE_URL
    ) as checkpointer:
        await checkpointer.setup()

        agent = create_agent(
            model=llm,
            tools=[],
            system_prompt="You are a helpful assistant!. ignore empty message",
            checkpointer=checkpointer,
            middleware=[welcome_back_message],
        )
        yield agent
