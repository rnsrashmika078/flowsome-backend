from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from api.routes import router
import json
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from core.config import settings
from schemas.models.lang.chatModels import local, simple_model, complex_model
from schemas.services.middleware.customMiddlewares import dynamic_model_middleware
from langchain.agents.middleware import (
    FilesystemFileSearchMiddleware,
    SummarizationMiddleware,
)
from schemas.models.lang.chatModels import summarizeModel
import dotenv
import os
from schemas.tools.index import read_file_tool, read_image
from fastapi.staticfiles import StaticFiles

from utils.helper import init_create_agent

dotenv.load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(
        settings.DATABASE_URL
    ) as checkpointer:

        await checkpointer.setup()

        app.state.checkpointer = checkpointer
        app.state.root_path = r"C:\Users\Rashm\OneDrive\Desktop\path"
        app.state.agent = init_create_agent(checkpointer, app.state.root_path)
        yield


app = FastAPI(lifespan=lifespan)

# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://192.168.1.105:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
