
from app.rag.ingest import get_collection


def retrieve_documents(question: str, top_k: int = 3) -> list[dict]:
    question = question.strip()

    if not question:
        return []

    collection = get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return [
        {
            "content": document,
            "source": metadata.get("source", "unknown"),
            "distance": distance,
        }
        for document, metadata, distance
        in zip(documents, metadatas, distances)
    ]
