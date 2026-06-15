import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from config import (
    EMBEDDING_MODEL, CHROMA_PATH, CHROMA_COLLECTION,
    N_RESULTS, GROQ_API_KEY, LLM_MODEL
)


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


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Format retrieved chunks into a grounded prompt."""
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(
            f"[Document {i} — {chunk['source']}]\n{chunk['text']}"
        )
    context = "\n\n".join(context_blocks)

    return f"""You are a helpful assistant for college students looking for off-campus housing.
Answer the question using ONLY the information provided in the documents below.
If the documents do not contain enough information to answer the question, say:
"I don't have enough information on that in my current sources."

Do not use any outside knowledge. Do not list sources at the end — they will be provided separately.

Documents:
{context}

Question: {query}

Answer:"""


def generate(query: str, chunks: list[dict]) -> dict:
    """Call the Groq LLM with retrieved chunks and return a grounded answer."""
    client = Groq(api_key=GROQ_API_KEY)
    prompt = build_prompt(query, chunks)

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,   # low temperature = more grounded, less creative
    )

    answer = response.choices[0].message.content

    # Collect unique sources from retrieved chunks
    sources = list({f"{c['source']} — {c['url']}" for c in chunks if c["url"]})

    return {
        "answer":  answer,
        "sources": sources,
        "chunks":  chunks,
    }


def ask(query: str, model, collection) -> dict:
    """Full pipeline: retrieve chunks → generate grounded answer."""
    chunks = retrieve(query, model, collection)
    return generate(query, chunks)


# ── TEST BLOCK ────────────────────────────────────────────────────────
if __name__ == "__main__":
    TEST_QUERIES = [
        "How much income do I need to qualify to rent an apartment?",
        "What are the warning signs that a rental listing might be a scam?",
        "What should I look for when inspecting an apartment before moving in?",
        "What fees beyond monthly rent should I ask about before signing a lease?",
        "How to find a compatible roommate?",
        # Out-of-scope — system should decline
        "What is the best laptop to buy for college?",
    ]

    model, collection = get_retriever()

    for query in TEST_QUERIES:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        result = ask(query, model, collection)
        print(result["answer"])
        print("\nSources:")
        for s in result["sources"]:
            print(f"  • {s}")