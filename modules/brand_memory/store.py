"""
store.py — Brand Memory Document Store (Vector-Backed)
Stores brand/company documents (about us, policies, FAQs, PDFs of
brochures/contracts, tone-of-voice guides, etc.) and indexes them for
semantic retrieval:

  SQLite (brand_memory_store.db) -> document METADATA + full text
      (id, title, content, tags, source_type, created_at)
  ChromaDB (chroma_db/)          -> chunk-level VECTOR EMBEDDINGS
      used for similarity search at query time (see vector_store.py)

Ingestion flow for any document (plain text or PDF):
  1. Extract raw text (pdf_utils.extract_text_from_pdf for PDFs; passed
     straight through for plain text).
  2. Chunk it into overlapping word-windows (pdf_utils.chunk_text).
  3. Embed each chunk (embeddings.embed_batch) and upsert into ChromaDB
     (vector_store.add_chunks), tagged with the document's id/title.
  4. Save the document's metadata + full text in SQLite for listing/audit.
"""

import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone

from .pdf_utils import extract_text_from_pdf, chunk_text
from . import vector_store

DB_FILE = os.path.join(os.path.dirname(__file__), "brand_memory_store.db")


def _get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_brand_db():
    """Initialize local brand memory database. Idempotent -- safe on every startup."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS brand_documents (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL,
            tags        TEXT,
            source_type TEXT DEFAULT 'text',
            chunk_count INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    _seed_default_docs()


def _seed_default_docs():
    """Seed a couple of starter brand documents if the store is empty."""
    if list_documents():
        return

    starter_docs = [
        {
            "title": "Brand Voice & Tone Guide",
            "tags": "brand,tone,voice",
            "content": (
                "RealEstate AI speaks with confidence, warmth, and transparency. "
                "We never exaggerate numbers or make guarantees we can't back with data. "
                "Our tone is professional but approachable -- we explain jargon rather than "
                "hide behind it. We favor clear, benefit-led language over hype. "
                "We always disclose when pricing or availability may change, and we "
                "highlight verified information (NOC status, title verification) prominently "
                "because trust is our biggest differentiator in the Pakistani property market."
            ),
        },
        {
            "title": "Company Overview",
            "tags": "about,company,overview",
            "content": (
                "RealEstate AI is a Pakistan-focused property intelligence platform. "
                "We combine AI-driven competitor analysis, customer review intelligence, "
                "buyer persona profiling, and hyper-personalized advertising to help "
                "property teams market smarter and close leads faster. Our platform "
                "primarily serves agencies and developers operating in Karachi, Lahore, "
                "and Islamabad, with data sourced from Zameen.com and verified customer "
                "feedback."
            ),
        },
        {
            "title": "Standard Disclaimers & Compliance Notes",
            "tags": "policy,compliance,disclaimer",
            "content": (
                "All marketing content must avoid guaranteeing investment returns. Use "
                "phrases like 'historically has seen' or 'can offer' instead of 'will earn'. "
                "Do not publish a property's exact address without owner consent. Always "
                "verify NOC (No Objection Certificate) status before claiming a project is "
                "'fully approved'. Pricing shown in ads should include a 'subject to change' "
                "note if sourced from third-party listings."
            ),
        },
    ]
    for doc in starter_docs:
        add_document(doc["title"], doc["content"], doc.get("tags", ""))


def _ingest(title: str, content: str, tags: str, source_type: str) -> dict:
    """Shared ingestion pipeline: chunk -> embed -> vector store -> SQLite metadata."""
    title = (title or "").strip()[:200]
    content = (content or "").strip()
    if not title or not content:
        return {"success": False, "error": "title and content are required"}

    doc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    chunks = chunk_text(content)
    if not chunks:
        return {"success": False, "error": "no extractable text found in document"}

    # 1. Embed + index chunks in ChromaDB
    vector_store.add_chunks(doc_id, title, chunks)

    # 2. Save metadata + full text in SQLite
    conn = _get_conn()
    conn.execute(
        "INSERT INTO brand_documents (id, title, content, tags, source_type, chunk_count, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (doc_id, title, content, tags or "", source_type, len(chunks), now),
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "id": doc_id,
        "title": title,
        "chunk_count": len(chunks),
        "created_at": now,
    }


def add_document(title: str, content: str, tags: str = "") -> dict:
    """Ingest a plain-text brand document (chunked + embedded into the vector index)."""
    return _ingest(title, content, tags, source_type="text")


def add_pdf_document(title: str, file_path: str, tags: str = "") -> dict:
    """
    Ingest a PDF brand document: extracts text page-by-page, then runs it
    through the same chunk -> embed -> index pipeline as plain text.
    """
    try:
        content = extract_text_from_pdf(file_path)
    except Exception as e:
        return {"success": False, "error": f"failed to read PDF: {e}"}

    if not content.strip():
        return {"success": False, "error": "no extractable text found in PDF (it may be a scanned image without a text layer)"}

    title = title or os.path.splitext(os.path.basename(file_path))[0]
    return _ingest(title, content, tags, source_type="pdf")


def delete_document(doc_id: str) -> dict:
    """Delete a document's metadata (SQLite) and its vectors (ChromaDB)."""
    conn = _get_conn()
    cur = conn.execute("DELETE FROM brand_documents WHERE id = ?", (doc_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()

    if deleted:
        vector_store.delete_document_chunks(doc_id)
    return {"success": deleted}


def list_documents() -> list:
    """Return all documents, most recent first (content truncated for listing)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, content, tags, source_type, chunk_count, created_at "
        "FROM brand_documents ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "preview": (r["content"][:160] + "...") if len(r["content"]) > 160 else r["content"],
            "tags": r["tags"],
            "source_type": r["source_type"],
            "chunk_count": r["chunk_count"],
            "created_at": r["created_at"],
            "char_count": len(r["content"]),
        }
        for r in rows
    ]


STOP_WORDS = {
    "the", "a", "an", "is", "in", "it", "and", "to", "of", "for", "was",
    "are", "with", "this", "that", "my", "on", "be", "i", "we", "they",
    "he", "she", "our", "very", "so", "but", "at", "from", "by", "not",
    "have", "has", "had", "do", "did", "its", "as", "or", "if", "you",
    "your", "will", "can", "what", "how", "when", "where", "why", "does",
    "give", "about", "should", "use", "using"
}


def _extract_keywords(text: str) -> list:
    words = re.findall(r"\b[a-zA-Z0-9']+\b", (text or "").lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def search_chunks(query: str, top_k: int = 4) -> list:
    """
    Hybrid search: retrieves semantic vector candidates from ChromaDB,
    scores candidate chunks against query keywords (with title/content weighting),
    and returns top_k re-ranked chunks.
    """
    raw_matches = vector_store.query(query, top_k=top_k * 3)
    if not raw_matches:
        return []

    q_keywords = _extract_keywords(query)
    if not q_keywords:
        return raw_matches[:top_k]

    scored = []
    for match in raw_matches:
        chunk_text = match["chunk"].lower()
        title_text = (match.get("doc_title") or "").lower()
        
        kw_score = 0.0
        for kw in q_keywords:
            if kw in title_text:
                kw_score += 3.0
            occurrences = chunk_text.count(kw)
            if occurrences > 0:
                kw_score += min(occurrences, 3) * 1.0

        combined_score = match["score"] + (kw_score * 0.25)
        match_copy = dict(match)
        match_copy["hybrid_score"] = round(combined_score, 3)
        scored.append(match_copy)

    scored.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return scored[:top_k]

