
import os
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


KNOWLEDGE_BASE = Path("/app/data/knowledge_base")
COLLECTION_NAME = "customer_support_policies"


def get_collection():
    chroma_host = os.getenv("CHROMA_HOST", "chromadb")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))

    client = chromadb.HttpClient(
        host=chroma_host,
        port=chroma_port,
    )

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )


def split_text(text: str, chunk_size: int = 800, overlap: int = 100):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def ingest_documents():
    if not KNOWLEDGE_BASE.exists():
        raise FileNotFoundError(
            f"Knowledge base not found: {KNOWLEDGE_BASE}"
        )

    collection = get_collection()
    files = sorted(KNOWLEDGE_BASE.glob("*.txt"))

    if not files:
        raise FileNotFoundError(
            f"No .txt policy files found in {KNOWLEDGE_BASE}"
        )

    for file_path in files:
        content = file_path.read_text(encoding="utf-8")
        chunks = split_text(content)

        if not chunks:
            continue

        ids = [
            f"{file_path.stem}-{i}"
            for i in range(len(chunks))
        ]

        collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=[
                {"source": file_path.name}
                for _ in chunks
            ],
        )

        print(
            f"Ingested {len(chunks)} chunks from {file_path.name}"
        )

    print(f"Total indexed chunks: {collection.count()}")


if __name__ == "__main__":
    ingest_documents()
