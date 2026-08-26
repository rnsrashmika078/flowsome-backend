from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from api.routes import router
import json
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from core.config import settings
from schemas.models.lang.chatModels import local, simple_model,complex_model
from schemas.services.middleware.customMiddlewares import dynamic_model_middleware
from langchain.agents.middleware import SummarizationMiddleware
from schemas.models.lang.chatModels import summarizeModel
import dotenv
import os
from schemas.tools.index import read_file_tool, read_image
from fastapi.staticfiles import StaticFiles

dotenv.load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(
        settings.DATABASE_URL
    ) as checkpointer:

        await checkpointer.setup()

        app.state.agent = create_agent(
            model=local,
            # tools=[read_file_tool,read_image],
            system_prompt="You are a helpful assistant!. Tools Available: read_file_tool -> read files , read_image -> image read",
            checkpointer=checkpointer,
        #     middleware=[
        #         dynamic_model_middleware, 
        #         SummarizationMiddleware(
        #             model=summarizeModel,
        #             trigger=("tokens", 4000),
        #             keep=("messages", 20),
        # ),],
        )
        yield


app = FastAPI(lifespan=lifespan)

# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000" , "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
