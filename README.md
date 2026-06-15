# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

My domain is off-campus housing handbook. It includes step-by-step guides on how to calculate what you can afford, considering hidden costs like utilities, deposits, and parking. It has explanations of lease terms (like joint vs. individual leases), how a guarantor works, and what to watch out for before signing. It also summaries of local laws outlining what a landlord is legally required to provide (like timely repairs) and what your obligations are as a tenant. User will can also find tips on avoiding rental scams, securing your apartment, and registering guests and advice on finding roommates, setting up chore charts, and drafting roommate agreements. Finding off-campus housing handbooks through official university channels is difficult because institutions intentionally distance themselves from the private rental market to avoid legal liability If a school endorses specific landlords or properties, they risk being blamed for lease disputes, scams, or poor living conditions.

---

## Document Sources

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Redfin Blog | A student's guide on how to find off-campus housing | https://www.redfin.com/blog/how-to-find-off-campus-housing/  |
| 2 | Redfin Blog | How to rent an apartment as an international student study in the USA| https://www.redfin.com/blog/international-student-renting-guide/ |
| 3 | Find My Place | 9 best ways students can find off-campus housing near their university in 2026 | https://findmyplace.co/blog/find-off-campus-housing-near-university-2026/ |
| 4 | Tuition Rewards | Tips for finding off-campus housing | https://www.tuitionrewards.com/newsroom/articles/570/tips-for-finding-off-campus-housing |
| 5 | Apartments.com | 11 tips for first time renters | https://www.apartments.com/blog/first-time-apartment-renter-tips |
| 6 | Texas Apartment Association | Everything you need to know about lease termination | https://www.taa.org/resources/lease-termination/ |
| 7 | Texas Apartment Association | Explaining the process for applying for rental housing | https://www.taa.org/resources/applying-for-rental-housing/ |
| 8 | Apartments.com | A roommate considerations checklist | `documents/roommate-considerations-checklist.pdf` |
| 9 | Detb.org | Ways to save money in college | https://www.debt.org/students/college-budgeting-101/ |
| 10 | Texas Apartment Association | A list of assisstance available when you have trouble paying rent | https://www.taa.org/resources/rental-assistance/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 150–250 tokens for blog articles; 60–120 tokens for the checklist PDF (source 8)

**Overlap:** 30-50 tokens

**Why these choices fit your documents:** The blog articles (sources 1–7, 9–10) are structured with subheaders, where each section contains a short intro paragraph and a bullet list covering one focused topic (e.g., "Watch out for hidden fees" or "Inspect the property condition"). Each of these sections averages 150–250 tokens and represents a complete, self-contained idea that maps directly to the kinds of questions a user would ask. Chunking at the subheader level keeps each chunk topically coherent and avoids merging unrelated sections together.

The roommate considerations checklist PDF (source 8) is already pre-divided into labeled categories (e.g., Lifestyle, Chores, Guests/Visitors, Pets, Parking). Each category is chunked as a unit, keeping the "ask yourself" and "ask your potential roommate" questions for the same category together. This preserves the self-reflection and conversation-starter pairing that makes the checklist useful as a retrieval result.

An overlap of 30–50 tokens (~1–2 sentences or the final bullet of the preceding section) handles cases where a closing sentence in one section introduces the next topic, ensuring no bridging context is lost between chunks.

Each chunk will be tagged with its source URL (or file path for source 8) and a topic label (e.g., `budgeting`, `lease`, `roommates`, `scams`) at ingestion time to improve retrieval precision and avoid returning duplicate chunks from the same domain.

**Final chunk count:** 103 chunks across 10 documents

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2`

**Top-k:** 5

**Production tradeoff reflection:**
`all-MiniLM-L6-v2` is a practical choice for this project — it's lightweight, fast, and handles general English prose well. However, in a real deployment with no cost constraint, several tradeoffs would be worth evaluating:

- **Context length:** `all-MiniLM-L6-v2` has a 256-token limit, which fits our 150–250 token chunks comfortably. A model like `text-embedding-3-large` (OpenAI) or `nomic-embed-text` supports longer contexts, which would matter if chunks were larger or if we embedded entire sections at once.

- **Accuracy on domain-specific text:** Housing and rental terminology (e.g., "security deposit," "co-signer," "lease termination") is common enough that a general-purpose model handles it reasonably well. For a more specialized domain (e.g., medical or legal),a domain-fine-tuned model would meaningfully outperform MiniLM.

- **Multilingual support:** Source 2 targets international students, and real users may query in languages other than English. A model like `paraphrase-multilingual-MiniLM-L12-v2`or `multilingual-e5-large` would be worth the added size and latency for that use case.

- **Latency vs. accuracy:** Larger models like `bge-large-en-v1.5` or OpenAI's
  `text-embedding-3-large` produce more accurate embeddings but take longer to run at query time. For a student housing assistant with relatively simple queries, the accuracy gain may not justify the latency cost.

**Why top-k = 5:** Retrieving 5 chunks gives the LLM enough context to synthesize an answer that draws on multiple relevant subtopics (e.g., a question about moving in might touch on security deposits, property inspection, and hidden fees) without flooding the context window with noise. Too few chunks (k=1–2) risks missing relevant information when a query spans multiple sections; too many (k=10+) risks diluting the relevant content with loosely related chunks, which can confuse the model or push the most relevant content out of focus.

**Why semantic search works without exact word matches:** Embedding models map text into a high-dimensional vector space where meaning is encoded geometrically — chunks and queries that share the same concept end up close together even when the words differ. For example, a query like "what should I check before signing?" will retrieve chunks about lease agreements and hidden fees because the model has learned that "signing" and "lease agreement" are semantically related, even if the word "signing" never appears in the chunk.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain the mechanism. -->

**System prompt grounding instruction:** The LLM is instructed via the prompt template in `build_prompt()` in `query.py`:
"You are a helpful assistant for college students looking for off-campus housing.
Answer the question using ONLY the information provided in the documents below.
If the documents do not contain enough information to answer the question, say: "I don't have enough information on that in my current sources."

Do not use any outside knowledge. Do not list sources at the end — they will be provided separately."

The retrieved chunks are injected into the prompt as numbered, labeled context 
blocks before the question:

[Document 1 — Redfin Blog]
`<chunk text>`

[Document 2 — Tuition Rewards]
`<chunk text>`

...

Question: `<user query>`

Answer:

The temperature is set to 0.2 (via `client.chat.completions.create(..., temperature=0.2)`)  to reduce creative generation and keep responses close to the retrieved content.

**How source attribution is surfaced in the response:**
Source attribution is handled programmatically, not left to the LLM. After generation, the `generate()` function in `query.py` collects the `source` and `url` fields from each retrieved chunk's metadata and deduplicates them:

```python
sources = list({f"{c['source']} — {c['url']}" for c in chunks if c["url"]})
```

These are returned alongside the answer and displayed separately in both the terminal output and the Gradio UI under a "Retrieved from" label. This guarantees attribution is always present and always accurate, regardless of what the LLM includes in its answer text.


---

## Evaluation Report

| # | Question | Expected Answer | System Response | Accuracy |
|---|----------|-----------------|-----------------|----------|
| 1 | How much income do I need to qualify to rent an apartment? | Landlords typically require 3x the monthly rent. A co-signer can satisfy the requirement if you don't meet the threshold. | Correctly stated 2–3x monthly rent rule with co-signer option, drawn from Redfin Blog and Tuition Rewards. | Accurate |
| 2 | What should I look for when inspecting an apartment before moving in? | Check structural issues, appliances, plumbing, electrical outlets, and pests. Photograph existing damage before signing. | Returned neighborhood research chunks instead of the inspection checklist on first retrieval pass. After min_length fix, the LLM synthesized a correct answer from partial context. | Partially accurate |
| 3 | What are the warning signs that a rental listing might be a scam? | Red flags include unusually low rent, landlord out of country, requests for money before seeing the unit, and vague photos. | Correctly returned 10 specific red flags drawn from Redfin Blog and Apartments.com, matching expected answer and adding additional detail. | Accurate |
| 4 | What fees beyond monthly rent should I ask about before signing a lease? | Application fees, pet fees, parking fees, amenity fees, and early termination fees. | Correctly listed all 5 fee types with descriptions, sourced from Redfin Blog. | Accurate |
| 5 | How to find a compatible roommate? | Discuss lifestyle expectations — cleanliness, guests, schedules, bills — before committing to a roommate. | Correctly drew from the Apartments.com checklist and Redfin Blog to cover compatibility questions and search methods. | Accurate |

**Out-of-scope test:** "What is the best laptop to buy for college?"
System responded: *"I don't have enough information on that in my current sources."* — grounding enforcement working correctly.

---

## Failure Case

**Query 2 — apartment inspection retrieval failure**

When asked "What should I look for when inspecting an apartment before moving in?", 
the retriever returned neighborhood research chunks instead of the inspection checklist 
that exists in the Redfin PDF.

**Why it happened:** The Redfin article has a section titled "Inspect the property condition" followed by a bullet list of 5 items (structural issues, appliances, plumbing, electrical, pests). During chunking, `is_section_header()` correctly identified "Inspect the property condition" as a header and split it off as the start of a new chunk — but the header line itself is only 32 characters, just above the `min_length = 150` threshold after the fix. The resulting chunk starts with the header but the embedding model weighted the surrounding context (broker fees section immediately before it in the PDF) more heavily than the inspection content itself, causing the vector to drift toward general property research rather than pre-move-in inspection.

**What this means for the pipeline:** This is a boundary sensitivity problem in subheader-based chunking. When a section header is very short and the preceding section bleeds into the same chunk due to PDF page flow, the embedding loses specificity. A fix would be to prepend the section header as a context label to every chunk it produces — e.g. `"[Section: Inspect the property condition]\n..."` 
— so the embedding always carries the topic signal regardless of surrounding content.

---

## Spec Reflection

**One way the spec helped:** The chunking strategy section of planning.md directly 
shaped the implementation. Deciding upfront to split at subheader boundaries rather 
than fixed character windows meant the chunks matched the natural topic structure of 
the blog articles, which is why queries 3 and 4 retrieved well with distance scores 
under 0.6.

**One way implementation diverged:** The original spec planned to use Selenium and 
BeautifulSoup for web ingestion. During implementation, Redfin and other sites 
blocked automated scraping with anti-bot detection, so the pipeline was changed to 
PDF-only ingestion using pdfplumber. The architecture diagram and AI Tool Plan in 
planning.md were updated to reflect this before continuing.

---

## AI Usage

**Instance 1 — Ingestion and chunking code**
I provided Claude with my Documents table, Chunking Strategy section, and pipeline 
diagram and asked it to implement `ingest.py`. The generated code used a fixed 
character splitter initially. I redirected it to use subheader-based boundary 
detection instead, explaining that my documents were structured with section headers 
rather than uniform paragraph lengths. I also added the `clean_text()` function after 
inspecting chunk output and finding PDF artifacts (page URLs, timestamps, conference 
banners) that the first version didn't strip.

**Instance 2 — Generation prompt design**
I asked Claude to implement the `build_prompt()` function in `query.py`. The first 
version instructed the LLM to list sources at the end of its answer, which caused 
duplicate source output since my pipeline already appends sources programmatically 
from chunk metadata. I identified the duplication and directed Claude to remove the 
source-listing instruction from the prompt, keeping attribution handled entirely by 
the metadata pipeline.