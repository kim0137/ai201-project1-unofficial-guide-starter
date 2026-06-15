import chromadb
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, CHROMA_PATH, CHROMA_COLLECTION, N_RESULTS


def get_retriever():
    """Load the embedding model and ChromaDB collection."""
    model = SentenceTransformer(EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(CHROMA_COLLECTION)
    return model, collection


def retrieve(query: str, model, collection, n_results: int = N_RESULTS) -> list[dict]:
    """Return the top-k most relevant chunks for a query."""
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":     text,
            "source":   metadata["source"],
            "url":      metadata["url"],
            "topic":    metadata["topic"],
            "distance": round(distance, 4),
        })

    return chunks


if __name__ == "__main__":
    # Test with 3 of your 5 evaluation questions
    TEST_QUERIES = [
        "How much income do I need to qualify to rent an apartment?",
        "What should I look for when inspecting an apartment before moving in?",
        "What are the warning signs that a rental listing might be a scam?",
        "What fees beyond monthly rent should I ask about before signing a lease?",
        "How to find a compatible roommate?",
    ]

    model, collection = get_retriever()

    for query in TEST_QUERIES:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        chunks = retrieve(query, model, collection)
        for i, chunk in enumerate(chunks, 1):
            print(f"\n  Result {i} | distance: {chunk['distance']} | {chunk['source']}")
            print(f"  {chunk['text'][:300]}")
            print("  ---")