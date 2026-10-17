import json
import operator
import subprocess
from typing import Annotated, Literal, Optional
import os

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langgraph.config import get_stream_writer, get_config

# from IPython.display import Image, display
from langchain_ollama import ChatOllama

# from model import CustomState
from pydantic import BaseModel, Field

from utils.splitter import splitter
from utils.reader import read_pdf
from database.chroma import document_key, get_document_collection

# from utils.read_files import recall_project_structure

llm = ChatOllama(model="gemma4:e2b", reasoning=False, temperature=0.4)
import sys

MAX_RESULT_CHARS = 2000
MAX_SCRIPTS_IN_PROMPT = 2


# Graph state
class State(TypedDict):
    question: str
    text: str
    chunks: list[str]
    document_path: str
    stage: str
    context: str
    indexed: bool


class GeneratePythonScriptOutput(BaseModel):
    script: str = Field(..., description="Python script for user given task")


# Nodes
def check_index(
    state: State,
) -> dict:
    """check if the document is already embedded in the vector db"""

    writer = get_stream_writer()

    already_indexed = get_document_collection(state["document_path"]).count() > 0

    if already_indexed:
        writer({"message": "Document already indexed. Skipping embed, retrieving..."})

    return {"indexed": already_indexed}


def route_index(state: State) -> str:
    """skip reading/splitting/embedding when the document is already indexed"""

    return "retrieve_result" if state.get("indexed") else "read_document"


# Nodes
def read_document(
    state: State,
) -> dict:
    """read user given document using python library"""

    writer = get_stream_writer()
    writer({"message": f"Reading document..."})

    text = read_pdf(state["document_path"])

    if not text.strip():
        writer(
            {
                "message": "No extractable text found in the document "
                "(it may be a scanned/image-only PDF)."
            }
        )

    return {
        "text": text,
    }


# Nodes
def split_to_chunk(
    state: State,
) -> dict:
    """split read document text to chunks"""

    writer = get_stream_writer()
    writer({"message": "Splitting document text to chunk..."})

    chunks = splitter.split_text(state["text"])

    return {"chunks": chunks}


# Nodes
def embedding_and_store(
    state: State,
) -> dict:
    """Embedding and store in vector db..."""

    writer = get_stream_writer()
    writer({"message": "Embedding and store in vector db..."})

    chunks = state.get("chunks") or []

    if not chunks:
        writer({"message": "Nothing to embed: no text chunks were produced."})
        return {"stage": "EMPTY"}

    key = document_key(state["document_path"])
    doc_collection = get_document_collection(state["document_path"])
    doc_collection.upsert(
        ids=[f"{key}_{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source": state["document_path"]}] * len(chunks),
    )

    return {"stage": "EMBEDDED"}


# Nodes
def retrieve_result(
    state: State,
) -> dict:
    """Retrieving relaxant chunk..."""

    writer = get_stream_writer()
    writer({"message": "Retrieving relevant chunks..."})

    doc_collection = get_document_collection(state["document_path"])
    count = doc_collection.count()

    if count == 0:
        return {"context": ""}

    results = doc_collection.query(
        query_texts=[state["question"]],
        n_results=min(3, count),
    )

    context = "\n\n".join(results["documents"][0])

    return {"context": context}
