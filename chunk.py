import re

def chunk_blog(doc: dict) -> list[dict]:
    """Split on lines that look like section headers (short, no period at end)."""
    lines = doc["text"].split("\n")
    chunks = []
    current = []

    for line in lines:
        # Heuristic: a header is a short line (<60 chars) with no trailing period
        is_header = len(line.strip()) < 60 and not line.strip().endswith(".")
        if is_header and current:
            chunk_text = "\n".join(current).strip()
            if len(chunk_text) > 50:  # skip near-empty sections
                chunks.append({**doc, "text": chunk_text})
            current = [line]
        else:
            current.append(line)

    if current:
        chunk_text = "\n".join(current).strip()
        if chunk_text:
            chunks.append({**doc, "text": chunk_text})

    return chunks


def chunk_checklist(doc: dict) -> list[dict]:
    """Split on category headers (ALL CAPS lines or bold-looking lines)."""
    lines = doc["text"].split("\n")
    chunks = []
    current_label = "General"
    current = []

    for line in lines:
        # Category headers in the checklist are short and ALL CAPS
        if line.strip().isupper() and len(line.strip()) > 3:
            if current:
                chunks.append({
                    **doc,
                    "text": "\n".join(current).strip(),
                    "topic": current_label.lower().replace(" ", "-")
                })
            current_label = line.strip()
            current = [line]
        else:
            current.append(line)

    if current:
        chunks.append({**doc, "text": "\n".join(current).strip(), "topic": current_label})

    return chunks