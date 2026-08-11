from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from api.routes import router
import json
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from core.config import settings
from schemas.models.lang.chatModels import local, simple_model
from schemas.services.middleware.customMiddlewares import dynamic_model_middleware
import dotenv

dotenv.load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with AsyncPostgresSaver.from_conn_string(
        settings.DATABASE_URL
    ) as checkpointer:

        await checkpointer.setup()

        app.state.agent = create_agent(
            model=local,
            tools=[],
            system_prompt="You are a helpful assistant!",
            checkpointer=checkpointer,
            middleware=[dynamic_model_middleware],
        )

        yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
