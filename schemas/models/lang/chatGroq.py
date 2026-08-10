from langchain_groq import ChatGroq
from core.config import settings
from langchain.agents import create_agent

# from langgraph.checkpoint.postgres import PostgresSaver
from core.config import settings
from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# from ..middleware.customMiddlewares import (
#     dynamic_model_middleware,
# )

simple_model = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.chat_model_text,
    temperature=0,
    max_tokens=None,
    # reasoning_format="parsed",
    timeout=None,
    max_retries=2,
)
complex_model = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.chat_model_file,
    temperature=0,
    reasoning_format="hidden",
    reasoning_effort="none",
    # reasoning_format="parsed",
    timeout=None,
    max_retries=2,
)


async def get_agent():
    async with AsyncPostgresSaver.from_conn_string(
        settings.DATABASE_URL
    ) as checkpointer:
        await checkpointer.setup()

        from schemas.services.middleware.customMiddlewares import (
            dynamic_model_middleware,
        )

        agent = create_agent(
            model=simple_model,
            tools=[],
            system_prompt="You are a helpful assistant!",
            checkpointer=checkpointer,
            middleware=[dynamic_model_middleware],
        )
        yield agent
