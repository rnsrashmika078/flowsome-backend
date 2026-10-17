from pathlib import Path
from pypdf import PdfReader


def read_pdf(path: str | Path) -> str:
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text
