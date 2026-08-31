from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from api.routes import router
import json
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from core.config import settings
import dotenv

# from fastapi.staticfiles import StaticFiles
from database.index import Base
from utils.helper import init_create_agent
from database.index import engine

dotenv.load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with AsyncPostgresSaver.from_conn_string(
            settings.DATABASE_URL
        ) as checkpointer:

            await checkpointer.setup()

            app.state.checkpointer = checkpointer
            app.state.root_path = r"C:\Users\Rashm\OneDrive\Desktop\path"

            app.state.agent = await init_create_agent(checkpointer, app.state.root_path)
            yield
    except Exception as e:
        print(f"error: {str(e)}")
        raise


app = FastAPI(lifespan=lifespan)
Base.metadata.create_all(bind=engine)
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
