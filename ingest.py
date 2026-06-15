import os
from config import DOCS_PATH
import pdfplumber
import re

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


def clean_text(text: str) -> str:
    """Remove PDF artifacts: page headers/footers, URLs, timestamps, short noise lines."""
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue
        # Skip lines that are just URLs
        if re.match(r'^https?://\S+$', stripped):
            continue
        # Skip page number patterns like "3/7" or "Page 3 of 7"
        if re.match(r'^\d+/\d+$', stripped):
            continue
        # Skip timestamps like "6/14/26, 10:48 PM"
        if re.match(r'^\d+/\d+/\d+,?\s+\d+:\d+\s*(AM|PM)', stripped):
            continue
        # Skip lines that are just a site title repeated as header (under 6 words, no period)
        if len(stripped.split()) <= 5 and not stripped.endswith("."):
            # keep if it looks like a real section header (will be caught by chunker)
            # skip if it looks like a nav/banner artifact
            if any(kw in stripped.lower() for kw in ["conference", "register", "sign up", "log in", "subscribe", "events"
                                                       "copyright", "all rights reserved",
                                                       "cookie", "privacy", "terms"]):
                continue

        cleaned.append(line)

    return "\n".join(cleaned)


def load_documents() -> list[dict]:
    """Load all PDF documents from the documents folder."""
    documents = []

    for filename in sorted(os.listdir(DOCS_PATH)):
        if not filename.endswith(".pdf"):
            continue

        filepath = os.path.join(DOCS_PATH, filename)

        with pdfplumber.open(filepath) as pdf:
            # Join pages with double newline, skip pages with no text
            raw_pages = [
                page.extract_text() for page in pdf.pages if page.extract_text()
            ]
            text = "\n\n".join(raw_pages)

        text = clean_text(text)

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
      - Blog articles  : split at section headers — a header is a short line
                         (<60 chars) that doesn't end with punctuation AND
                         is followed by body text (not another short line).
                         This prevents bullet points from being treated as headers.
      - Checklist PDF  : split at ALL CAPS category labels.
      - min_length = 80 characters: filters near-empty sections.
    """
    min_length = 80
    prefix = doc["filename"].replace(".pdf", "").replace(" ", "_").replace("-", "_").lower()
    lines = doc["text"].split("\n")
    chunks = []
    current = []
    counter = 0

    is_checklist = doc["topic"] == "roommates"

    def is_section_header(line: str, next_line: str = "") -> bool:
        s = line.strip()
        if not s:
            return False
        if is_checklist:
            return s.isupper() and len(s) > 3
        # For blogs: short line, no trailing punctuation, and the next line
        # is longer (meaning this is a heading, not a bullet fragment)
        is_short = len(s) < 60
        no_punct = not s.endswith((".", ",", ":", "?", "↑"))
        next_is_body = len(next_line.strip()) > 60
        return is_short and no_punct and next_is_body

    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else ""

        if is_section_header(line, next_line) and current:
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
        print(f"{doc['source']}: {len(chunks)} chunks")

    print(f"\nTotal chunks: {len(all_chunks)}")

    import random
    print("\n── 5 random chunks ──")
    for chunk in random.sample(all_chunks, min(5, len(all_chunks))):
        print(f"\n[{chunk['chunk_id']} | {chunk['topic']}]")
        print(chunk["text"][:400])
        print("---")