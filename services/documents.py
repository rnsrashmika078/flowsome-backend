from io import BytesIO
from pathlib import Path

import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


def read_pdf(source: str | Path) -> str:
    if isinstance(source, str) and source.startswith(("http://", "https://")):
        response = requests.get(source, timeout=30)
        response.raise_for_status()
        reader = PdfReader(BytesIO(response.content))
    else:
        reader = PdfReader(source)

    return "\n".join(page.extract_text() or "" for page in reader.pages)
