import chromadb
from config import CHROMA_PATH, CHROMA_COLLECTION

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection(CHROMA_COLLECTION)

# How many chunks are stored?
print(f"Total chunks: {collection.count()}")

# Peek at the first 5 stored chunks
results = collection.peek(5)
for i, (doc_id, text, metadata) in enumerate(zip(
    results["ids"],
    results["documents"],
    results["metadatas"]
)):
    print(f"\n[{i+1}] ID: {doc_id}")
    print(f"     Source: {metadata['source']} | Topic: {metadata['topic']}")
    print(f"     Text: {text[:200]}")