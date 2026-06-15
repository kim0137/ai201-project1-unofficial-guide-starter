import os
from config import DOCS_PATH
import pdfplumber

# Metadata for each PDF — mirrors the Documents table in planning.md
PDF_METADATA = {
    "how-to-find-off-campus-housing-redfin.pdf": {
        "source": "Redfin Blog",
        "url": "https://www.redfin.com/blog/how-to-find-off-campus-housing/",
        "topic": "finding-housing",
    },
    "how-to-rent-an-apartment-as-an-international-student-redfin.pdf": {
        "source": "Redfin Blog",
        "url": "https://www.redfin.com/blog/international-student-renting-guide/",
        "topic": ["renting-housing", "international-student"]
    },
    "the-9-best-ways-to-find-off-campus-housing-in-2026-find-my-place.pdf": {
        "source": "Find My Place",
        "url": "https://findmyplace.co/blog/find-off-campus-housing-near-university-2026/",
        "topic": ["finding-housing", "near-campus"]
    },
    "tips-for-finding-cheap-off-campus-housing-tuition-rewards-by-SAGE-scholars.pdf": {
        "source": "Tuition Rewards",   
        "url": "https://www.tuitionrewards.com/blog/cheap-off-campus-housing-tips/",
        "topic": "finding-housing",
    },
    "the-11-tips-for-first-time-renters-apartments.com.pdf": {
        "source": "Apartments.com",
        "url": "https://www.apartments.com/blog/first-time-apartment-renter-tips",
        "topic": ["renting-housing", "first-time-renter"]
    },
    "lease-termination-texas-apartment-association.pdf": {
        "source": "Texas Apartment Association",
        "url": "https://www.taa.org/resources/lease-termination/",
        "topic": "lease-termination",
    },
    "applying-for-rental-housing-Texas-Apartment-Association.pdf": {
        "source": "Texas Apartment Association",
        "url": "https://www.taa.org/resources/applying-for-rental-housing/",
        "topic": "applying-housing",
    },
    "roommate-considerations-checklist.pdf": {
        "source": "Apartments.com",
        "url": "https://www.apartments.com",
        "topic": "roommates",
    },
    "how-to-save-money-and-cut-expenses-in-college-Debt.org.pdf": {
        "source": "Debt.org",
        "url": "https://www.debt.org/students/college-budgeting-101/",
        "topic": ["budgeting", "college-budgeting"]
    },
    "rental-assistance-Texas-Apartment-Association.pdf": {
        "source": "Texas Apartment Association",
        "url": "https://www.taa.org/resources/rental-assistance/",
        "topic": ["rental-assistance", "paying-rent"]
    }
    
}

def load_documents() -> list[dict]:
    """Load all PDF documents from the documents folder."""
    documents = []

    for filename in sorted(os.listdir(DOCS_PATH)):
        if not filename.endswith(".pdf"):
            continue

        filepath = os.path.join(DOCS_PATH, filename)

        with pdfplumber.open(filepath) as pdf:
            text = "\n\n".join(
                page.extract_text()
                for page in pdf.pages
                if page.extract_text()
            )

        metadata = PDF_METADATA.get(filename, {
            "source": filename.replace(".pdf", "").replace("_", " ").replace("-", " ").title(),
            "url": "",
            "topic": "general",
        })

        documents.append({
            "filename": filename,
            "text": text,
            **metadata,
        })

    print(f"Loaded {len(documents)} document(s): {[d['source'] for d in documents]}")
    return documents


def chunk_document(doc: dict) -> list[dict]:
    """
    Split a PDF document into chunks ready for embedding.

    Strategy: subheader-based splitting targeting 150-250 tokens per chunk.
      - Blog articles  : split at section boundaries (short lines with no
                         trailing period act as header signals)
      - Checklist PDF  : split at category headers (ALL CAPS lines)
      - min_length = 50 characters: filters out near-empty sections

    Returns a list of dicts, each with:
      - "text"     : the chunk text (str)
      - "source"   : the document source name, e.g. "Redfin Blog" (str)
      - "url"      : the original source URL (str)
      - "topic"    : the topic tag, e.g. "finding-housing" (str)
      - "chunk_id" : a unique identifier, e.g. "redfin_blog_0" (str)
    """
    min_length = 50
    prefix = doc["source"].lower().replace(" ", "_")
    lines = doc["text"].split("\n")
    chunks = []
    current = []
    counter = 0

    is_checklist = doc["topic"] == "roommates"

    for line in lines:
        stripped = line.strip()

        # Detect section boundary:
        # - Checklist: ALL CAPS lines signal a new category
        # - Blog: short lines (<60 chars) with no trailing period = header
        is_boundary = (
            (is_checklist and stripped.isupper() and len(stripped) > 3)
            or
            (not is_checklist and len(stripped) < 60 and stripped
             and not stripped.endswith(".") and not stripped.endswith(","))
        )

        if is_boundary and current:
            chunk_text = "\n".join(current).strip()
            if len(chunk_text) >= min_length:
                chunks.append({
                    "text": chunk_text,
                    "source": doc["source"],
                    "url": doc["url"],
                    "topic": doc["topic"],
                    "chunk_id": f"{prefix}_{counter}",
                })
                counter += 1
            current = [line]
        else:
            current.append(line)

    # Flush the last section
    if current:
        chunk_text = "\n".join(current).strip()
        if len(chunk_text) >= min_length:
            chunks.append({
                "text": chunk_text,
                "source": doc["source"],
                "url": doc["url"],
                "topic": doc["topic"],
                "chunk_id": f"{prefix}_{counter}",
            })

    return chunks


if __name__ == "__main__":
    docs = load_documents()

    all_chunks = []
    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
        print(f"\n{doc['source']}: {len(chunks)} chunks")

    print(f"\nTotal chunks: {len(all_chunks)}")

    # Print 5 samples to inspect
    import random
    print("\n── 5 random chunks ──")
    for chunk in random.sample(all_chunks, min(5, len(all_chunks))):
        print(f"\n[{chunk['chunk_id']} | {chunk['topic']}]")
        print(chunk["text"][:300])
        print("---")