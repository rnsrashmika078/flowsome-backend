from langchain.tools import ToolRuntime
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from database.vector_store import document_key, get_document_collection
from services.documents import read_pdf, text_splitter


class RagState(TypedDict):
    question: str
    text: str
    chunks: list[str]
    document_path: str
    stage: str
    context: str
    indexed: bool


def _check_index(state: RagState) -> dict:
    writer = get_stream_writer()
    already_indexed = get_document_collection(state["document_path"]).count() > 0

    if already_indexed:
        writer({"message": "Document already indexed. Skipping embed, retrieving..."})

    return {"indexed": already_indexed}


def _route_index(state: RagState) -> str:
    return "retrieve" if state.get("indexed") else "read"


def _read_document(state: RagState) -> dict:
    writer = get_stream_writer()
    writer({"message": "Reading document..."})

    text = read_pdf(state["document_path"])

    if not text.strip():
        writer(
            {
                "message": (
                    "No extractable text found in the document "
                    "(it may be a scanned/image-only PDF)."
                )
            }
        )

    return {"text": text}


def _split_to_chunks(state: RagState) -> dict:
    writer = get_stream_writer()
    writer({"message": "Splitting document text into chunks..."})

    return {"chunks": text_splitter.split_text(state["text"])}


def _embed_and_store(state: RagState) -> dict:
    writer = get_stream_writer()
    writer({"message": "Embedding and storing in the vector database..."})

    chunks = state.get("chunks") or []

    if not chunks:
        writer({"message": "Nothing to embed: no text chunks were produced."})
        return {"stage": "EMPTY"}

    key = document_key(state["document_path"])
    collection = get_document_collection(state["document_path"])
    collection.upsert(
        ids=[f"{key}_{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source": state["document_path"]}] * len(chunks),
    )

    return {"stage": "EMBEDDED"}


def _retrieve(state: RagState) -> dict:
    writer = get_stream_writer()
    writer({"message": "Retrieving relevant chunks..."})

    collection = get_document_collection(state["document_path"])
    count = collection.count()

    if count == 0:
        return {"context": ""}

    results = collection.query(
        query_texts=[state["question"]],
        n_results=min(3, count),
    )

    return {"context": "\n\n".join(results["documents"][0])}


def _build_graph():
    workflow = StateGraph(RagState)
    workflow.add_node("check_index", _check_index)
    workflow.add_node("read_document", _read_document)
    workflow.add_node("split_to_chunks", _split_to_chunks)
    workflow.add_node("embed_and_store", _embed_and_store)
    workflow.add_node("retrieve", _retrieve)

    workflow.add_edge(START, "check_index")
    workflow.add_conditional_edges(
        "check_index",
        _route_index,
        {"read": "read_document", "retrieve": "retrieve"},
    )
    workflow.add_edge("read_document", "split_to_chunks")
    workflow.add_edge("split_to_chunks", "embed_and_store")
    workflow.add_edge("embed_and_store", "retrieve")
    workflow.add_edge("retrieve", END)

    return workflow.compile()


def rag_tool(question: str, document_path: str, runtime: ToolRuntime):
    """Answer a question about a PDF using retrieval-augmented generation.

    Args:
        question: The question to answer about the document.
        document_path: A local file path or an http(s) URL pointing to a PDF.
    """
    writer = get_stream_writer()
    chain = _build_graph()
    full_state = {}

    for chunk in chain.stream(
        {"question": question, "document_path": document_path},
        stream_mode=["updates", "custom"],
        version="v2",
    ):
        if chunk["type"] == "updates":
            for node_state in chunk["data"].values():
                full_state.update(node_state)
        elif chunk["type"] == "custom":
            data = chunk["data"]
            message = (
                data
                if isinstance(data, str)
                else data.get("status") or data.get("message", "")
            )
            if message:
                writer({"message": str(message)})

    return {"context": full_state.get("context", "no context")}
