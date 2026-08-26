"""
vector_store.py — ChromaDB Vector Store
This is the vector index: it persists chunk embeddings to a local
ChromaDB collection (on disk under modules/brand_memory/chroma_db/) and
provides similarity search over them.

store.py writes to this when a document is ingested (add_chunks).
rag_engine.py reads from this (via store.search_chunks -> query) when
answering a question.
"""

import os

import chromadb
from chromadb.utils.embedding_functions import EmbeddingFunction

from .embeddings import embed_batch, EMBED_DIM

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "brand_knowledge"


class _BridgeEmbeddingFunction(EmbeddingFunction):
    """Adapts embeddings.embed_batch() to ChromaDB's EmbeddingFunction protocol."""

    def __call__(self, input):
        return embed_batch(list(input))

    @staticmethod
    def name() -> str:
        return "brand_memory_bridge_embedding"

    def get_config(self) -> dict:
        return {"dim": EMBED_DIM}

    @staticmethod
    def build_from_config(config: dict) -> "_BridgeEmbeddingFunction":
        return _BridgeEmbeddingFunction()


_collection = None


def _get_collection():
    """Lazily create/reuse the persistent ChromaDB collection."""
    global _collection
    if _collection is not None:
        return _collection
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_BridgeEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def add_chunks(doc_id: str, doc_title: str, chunks: list):
    """Embed a document's chunks and add them to the vector index."""
    if not chunks:
        return
    collection = _get_collection()
    ids = [f"{doc_id}::{i}" for i in range(len(chunks))]
    metadatas = [
        {"doc_id": doc_id, "doc_title": doc_title, "chunk_index": i}
        for i in range(len(chunks))
    ]
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)


def delete_document_chunks(doc_id: str):
    """Remove all vectors belonging to a document (called when a doc is deleted)."""
    collection = _get_collection()
    try:
        collection.delete(where={"doc_id": doc_id})
    except Exception as e:
        print(f"[brand_memory] vector delete error: {e}")


def query(question: str, top_k: int = 4) -> list:
    """
    Semantic similarity search: embed the question, find the top_k nearest
    chunks across all documents by cosine distance.
    Returns: list[dict] -> {chunk, doc_id, doc_title, score} (score = similarity, higher is better)
    """
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []

    results = collection.query(query_texts=[question], n_results=min(top_k, count))
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    dists = (results.get("distances") or [[]])[0]

    matches = []
    for chunk, meta, dist in zip(docs, metas, dists):
        similarity = round(max(0.0, 1 - dist), 3)  # cosine distance -> similarity
        matches.append({
            "chunk": chunk,
            "doc_id": meta.get("doc_id"),
            "doc_title": meta.get("doc_title"),
            "score": similarity,
        })
    return matches


def collection_size() -> int:
    return _get_collection().count()
