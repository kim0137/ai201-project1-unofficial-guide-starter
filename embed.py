import chromadb
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, CHROMA_PATH, CHROMA_COLLECTION
from ingest import load_documents, chunk_document


def build_vector_store():
    """Embed all chunks and load them into ChromaDB."""

    # --- Load and chunk all documents ---
    docs = load_documents()
    all_chunks = []
    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    print(f"Total chunks to embed: {len(all_chunks)}")

    # --- Set up embedding model ---
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # --- Set up ChromaDB ---
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Delete existing collection so re-runs start fresh
    try:
        client.delete_collection(CHROMA_COLLECTION)
        print(f"Cleared existing collection: {CHROMA_COLLECTION}")
    except Exception:
        pass

    collection = client.create_collection(CHROMA_COLLECTION)

    # --- Embed and store ---
    texts = [chunk["text"] for chunk in all_chunks]
    ids = [chunk["chunk_id"] for chunk in all_chunks]
    metadatas = [
        {
            "source": chunk["source"],
            "url":    chunk["url"],
            "topic":  chunk["topic"] if isinstance(chunk["topic"], str)
                      else ", ".join(chunk["topic"]),
        }
        for chunk in all_chunks
    ]

    print("Embedding chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Stored {collection.count()} chunks in ChromaDB at {CHROMA_PATH}")
    return collection


if __name__ == "__main__":
    build_vector_store()