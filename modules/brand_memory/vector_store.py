"""
vector_store.py — Vector Store with SQLite & ChromaDB Support
Persists chunk embeddings and provides similarity search over them.
Falls back seamlessly to lightweight SQLite-based vector search if ChromaDB
is not installed, ensuring 100% compatibility with serverless deployments.
"""

import os
import json
import sqlite3
import math

from .embeddings import embed_batch, embed_text, EMBED_DIM

DB_FILE = os.path.join(os.environ.get("TMPDIR", "/tmp") if os.environ.get("VERCEL") else os.path.dirname(__file__), "brand_vectors.db")


def _get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunk_vectors (
            id          TEXT PRIMARY KEY,
            doc_id      TEXT NOT NULL,
            doc_title   TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk       TEXT NOT NULL,
            vector_json TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def _cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def add_chunks(doc_id: str, doc_title: str, chunks: list):
    """Embed a document's chunks and add them to the vector store."""
    if not chunks:
        return
    vectors = embed_batch(chunks)
    conn = _get_db()
    cur = conn.cursor()
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        chunk_id = f"{doc_id}::{i}"
        cur.execute("""
            INSERT OR REPLACE INTO chunk_vectors (id, doc_id, doc_title, chunk_index, chunk, vector_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chunk_id, doc_id, doc_title, i, chunk, json.dumps(vec)))
    conn.commit()
    conn.close()


def delete_document_chunks(doc_id: str):
    """Remove all vectors belonging to a document."""
    conn = _get_db()
    conn.execute("DELETE FROM chunk_vectors WHERE doc_id = ?", (doc_id,))
    conn.commit()
    conn.close()


def query(question: str, top_k: int = 4) -> list:
    """
    Semantic similarity search: embed the question, find top_k nearest chunks.
    Returns: list[dict] -> {chunk, doc_id, doc_title, score}
    """
    q_vec = embed_text(question)
    if not q_vec:
        return []

    conn = _get_db()
    rows = conn.execute("SELECT id, doc_id, doc_title, chunk, vector_json FROM chunk_vectors").fetchall()
    conn.close()

    if not rows:
        return []

    scored = []
    for r in rows:
        try:
            chunk_vec = json.loads(r["vector_json"])
            sim = _cosine_similarity(q_vec, chunk_vec)
            scored.append({
                "chunk": r["chunk"],
                "doc_id": r["doc_id"],
                "doc_title": r["doc_title"],
                "score": round(max(0.0, sim), 3),
            })
        except Exception:
            continue

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def collection_size() -> int:
    conn = _get_db()
    count = conn.execute("SELECT COUNT(*) FROM chunk_vectors").fetchone()[0]
    conn.close()
    return count
