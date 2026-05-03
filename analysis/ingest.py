import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib

# Section-aware chunk sizes — different sections need different granularity
SECTION_CHUNK_CONFIG = {
    "Item 1":          {"size": 1000, "overlap": 150},
    "Item 1A":         {"size": 600,  "overlap": 100},
    "Item 7":          {"size": 800,  "overlap": 150},
    "Item 8":          {"size": 500,  "overlap": 100},
    "default":         {"size": 800,  "overlap": 100},
}

SOURCE_RANK = {
    "sec_filing":           1.0,
    "sec.gov":              1.0,
    "earnings":             0.9,
    "investor":             0.85,
    "bloomberg.com":        0.75,
    "reuters.com":          0.75,
    "wsj.com":              0.70,
    "ft.com":               0.70,
    "seekingalpha.com":     0.45,
    "reddit.com":           0.15,
    "blog":                 0.20,
}

EARLY_STOP_CONFIDENCE = 0.82    # stop processing remaining URLs if we hit this
MAX_URLS_PER_ITEM     = 5
CHUNKS_PER_QUERY      = 5       # how many chunks to retrieve per source


def get_chroma_client(path: str = "./chroma_db"):
    client = chromadb.PersistentClient(path=path)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_or_create_collection(
        name="financial_analysis",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def ingest_filing_sections(
    ticker:   str,
    sections: dict,      # {section_name: text}
    form:     str,       # "10-K" or "10-Q"
    period:   str,       # "2024-09-28"
    collection
):
    """
    Ingests parsed filing sections with semantic-aware chunking.
    Each chunk gets rich metadata for filtered retrieval.
    """
    docs, ids, metadatas = [], [], []

    for section_name, text in sections.items():
        config = SECTION_CHUNK_CONFIG.get(section_name, SECTION_CHUNK_CONFIG["default"])

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config["size"],
            chunk_overlap=config["overlap"],
            separators=["\n\n", "\n", ". ", " "],
        )
        chunks = splitter.split_text(text)

        for i, chunk in enumerate(chunks):
            # Importance scoring — heuristic, adjust per your needs
            importance = score_chunk_importance(chunk, section_name)

            chunk_id = hashlib.md5(
                f"{ticker}_{form}_{period}_{section_name}_{i}".encode()
            ).hexdigest()

            docs.append(chunk)
            ids.append(chunk_id)
            metadatas.append({
                "ticker":           ticker,
                "form":             form,
                "period":           period,
                "section":          section_name,
                "chunk_index":      i,
                "total_chunks":     len(chunks),
                "importance_score": importance,
                "source_type":      "sec_filing",
                "source_rank":      SOURCE_RANK["sec_filing"],
            })

    collection.upsert(documents=docs, ids=ids, metadatas=metadatas)
    print(f"Ingested {len(docs)} chunks for {ticker} {form} {period}")


def ingest_web_document(
    ticker:      str,
    url:         str,
    text:        str,
    source_type: str,   # "earnings_transcript" | "investor_presentation" | "news" etc
    collection
):
    """Ingests web-sourced documents found during research."""
    config = SECTION_CHUNK_CONFIG["default"]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["size"],
        chunk_overlap=config["overlap"],
    )
    chunks = splitter.split_text(text)

    docs, ids, metadatas = [], [], []
    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{url}_{i}".encode()).hexdigest()
        docs.append(chunk)
        ids.append(chunk_id)
        metadatas.append({
            "ticker":           ticker,
            "url":              url,
            "source_type":      source_type,
            "source_rank":      SOURCE_RANK.get(source_type, 0.4),
            "chunk_index":      i,
            "importance_score": 0.5,   # web docs get neutral importance baseline
        })

    collection.upsert(documents=docs, ids=ids, metadatas=metadatas)


def score_chunk_importance(chunk: str, section: str) -> float:
    """
    Heuristic importance score for a chunk.
    Higher = retrieve first.
    """
    score = 0.5

    # Section-based baseline
    section_base = {
        "Item 7":   0.8,
        "Item 1A":  0.75,
        "Item 8":   0.7,
        "Item 1":   0.6,
    }
    score = section_base.get(section, 0.5)

    # Boost for financial keywords
    keywords = [
        "revenue", "decline", "increase", "risk", "growth",
        "margin", "cash", "debt", "guidance", "outlook",
        "significant", "material", "compared to prior year"
    ]
    hits = sum(1 for kw in keywords if kw.lower() in chunk.lower())
    score += min(hits * 0.03, 0.2)

    return round(min(score, 1.0), 3)


def hybrid_search(
    query:          str,
    ticker:         str,
    collection,
    section_filter: list[str] = None,
    source_types:   list[str] = None,
    k:              int = 8,
) -> list[dict]:
    """
    Semantic search with metadata filtering and importance re-ranking.
    """
    if section_filter or source_types:
        filters = [{"ticker": ticker}]
        if section_filter:
            filters.append({"section": {"$in": section_filter}})
        if source_types:
            filters.append({"source_type": {"$in": source_types}})
        where_clause = {"$and": filters}
    else:
        where_clause = {"ticker": ticker}

    print(where_clause)

    results = collection.query(
        query_texts=[query],
        n_results=k * 2,
        where=where_clause,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        semantic_score  = 1 - dist         # cosine distance → similarity
        importance      = meta.get("importance_score", 0.5)
        source_rank     = meta.get("source_rank", 0.5)

        # Combined score: semantic relevance + importance + source quality
        combined = (semantic_score * 0.6) + (importance * 0.25) + (source_rank * 0.15)

        chunks.append({
            "text":     doc,
            "metadata": meta,
            "score":    round(combined, 3),
        })

    # Re-rank and return top k
    chunks.sort(key=lambda x: x["score"], reverse=True)
    return chunks[:k]


SECTION_QUERY_MAP = {
    "revenue":        ["Item 7", "Item 1"],
    "margin":         ["Item 7", "Item 8"],
    "risk":           ["Item 1A", "Item 7"],
    "debt":           ["Item 8", "Item 7"],
    "cash":           ["Item 7", "Item 8"],
    "receivable":     ["Item 8", "Item 7"],
    "regulation":     ["Item 1A"],  # or add others as needed
    "product":        ["Item 1", "Item 7"],
    "guidance":       ["Item 7"],
    "acquisition":    ["Item 7", "Item 8"],
    "compensation":   ["Item 8"],
}

def infer_sections(query: str) -> list[str]:
    query_lower = query.lower()
    matched = []
    for keyword, sections in SECTION_QUERY_MAP.items():
        if keyword in query_lower:
            matched.extend(sections)
    return list(dict.fromkeys(matched)) or ["Item 7"]


def rank_url(url: str) -> float:
    url_lower = url.lower()
    for domain, score in SOURCE_RANK.items():
        if domain in url_lower:
            return score
    return 0.4


def classify_source_type(url: str) -> str:
    url_lower = url.lower()
    if "sec.gov"    in url_lower: return "sec_filing"
    if "earnings"   in url_lower: return "earnings_transcript"
    if "investor"   in url_lower: return "investor_presentation"
    return "news"


def chunk_web_content(text: str, url: str) -> list[str]:
    """
    Chunks web content with size tuned to source type.
    News articles get smaller chunks — more precise retrieval.
    Long-form documents (transcripts, presentations) get larger.
    """
    is_long_form = any(k in url.lower() for k in ["transcript", "investor", "presentation", "annual"])

    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = 900 if is_long_form else 600,
        chunk_overlap = 120 if is_long_form else 80,
        separators    = ["\n\n", "\n", ". ", " "],
    )
    return splitter.split_text(text)

collection = get_chroma_client()

def ingest_and_retrieve(
    url:     str,
    content: str,
    ticker:  str,
    query:   str,
) -> list[dict]:
    """
    Chunks a web document, ingests into vector DB,
    then immediately retrieves relevant chunks for the query.
    Returns ranked chunks — not the full document.
    """
    chunks     = chunk_web_content(content, url)
    source_type = classify_source_type(url)
    source_rank = rank_url(url)

    docs, ids, metadatas = [], [], []
    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{url}_{i}".encode()).hexdigest()
        docs.append(chunk)
        ids.append(chunk_id)
        metadatas.append({
            "ticker":      ticker,
            "url":         url,
            "source_type": source_type,
            "source_rank": source_rank,
            "chunk_index": i,
        })

    # Upsert — safe to call multiple times, deduplicates by ID
    collection.upsert(documents=docs, ids=ids, metadatas=metadatas)

    # Immediately retrieve relevant chunks for this specific query
    results = collection.query(
        query_texts=[query],
        n_results=CHUNKS_PER_QUERY,
        where={"url": url},       # filter to just this source
        include=["documents", "metadatas", "distances"]
    )

    retrieved = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        retrieved.append({
            "text":     doc,
            "metadata": meta,
            "score":    round((1 - dist) * source_rank, 3),   # discount by source quality
        })

    return sorted(retrieved, key=lambda x: x["score"], reverse=True)