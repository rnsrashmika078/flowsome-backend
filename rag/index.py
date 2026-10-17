from ollama import chat
from utils.splitter import splitter
from utils.reader import read_pdf

from database.chroma import collection
from pathlib import Path

# python -m rag.index

PDF_PATH = r"C:\Users\Rashm\Downloads\M.W.Rashmika Siriwardhana.pdf"


def main(pdf_path: str | Path, question: str = "what is the name of this candidate"):
    text = read_pdf(pdf_path)
    chunks = splitter.split_text(text)

    if not chunks:
        print("No text extracted from PDF.")
        return

    collection.add(
        ids=[f"pdf_{i}" for i in range(len(chunks))],
        documents=chunks,
    )

    results = collection.query(
        query_texts=[question],
        n_results=min(3, len(chunks)),
    )

    context = "\n\n".join(results["documents"][0])

    response = chat(
        model="gemma4:e2b",
        messages=[
            {
                "role": "user",
                "content": f"Answer following question concisely based on this PDF content:\n\n{context}\n\nQuestion: {question}",
            }
        ],
    )
    print(response.message.content)


if __name__ == "__main__":
    main(PDF_PATH)
