import hashlib

import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction,
)

embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_fn,
)


def document_key(document_path: str) -> str:
    return hashlib.sha1(str(document_path).encode("utf-8")).hexdigest()[:16]


def get_document_collection(document_path: str):
    return client.get_or_create_collection(
        name=f"document_{document_key(document_path)}",
        embedding_function=embedding_fn,
    )
