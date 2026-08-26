"""
embeddings.py — Vector Embeddings
Generates the vectors that ChromaDB indexes and searches over.

Two modes (same dual-mode pattern used everywhere else in this project):
  1. Gemini Embedding API (models/text-embedding-004) — real semantic
     embeddings, used automatically whenever GEMINI_API_KEY is set.
  2. Deterministic hashing fallback — a zero-cost, zero-dependency
     bag-of-words hash into a fixed-size vector. Not semantic, but keeps
     the whole pipeline (chunking → embed → ChromaDB → retrieval)
     fully functional offline / without an API key.

Both modes always return a vector of length EMBED_DIM so a single
ChromaDB collection can store either kind consistently.
"""

import os
import re
import json
import hashlib
import math

EMBED_DIM = 768  # matches Gemini text-embedding-004 default output size

STOP_WORDS = {
    "the", "a", "an", "is", "in", "it", "and", "to", "of", "for", "was",
    "are", "with", "this", "that", "my", "on", "be", "i", "we", "they",
    "he", "she", "our", "very", "so", "but", "at", "from", "by", "not",
    "have", "has", "had", "do", "did", "its", "as", "or", "if", "you",
    "your", "will", "can", "what", "how", "when", "where", "why",
}


def embed_text(text: str) -> list:
    """Return an EMBED_DIM-length vector for the given text."""
    vector = _try_gemini_embed(text)
    if vector is None:
        vector = _hashing_embed(text)
    return vector


def embed_batch(texts: list) -> list:
    """Convenience wrapper — embed a list of texts, one vector each."""
    return [embed_text(t) for t in texts]


# ---------------------------------------------------------------------------
# Gemini Embedding API
# ---------------------------------------------------------------------------

def _try_gemini_embed(text: str):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None

    try:
        import urllib.request

        body = json.dumps({
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": EMBED_DIM,
        }).encode()

        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"text-embedding-004:embedContent?key={api_key}")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST")

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        values = data["embedding"]["values"]
        if len(values) != EMBED_DIM:
            # pad/truncate defensively so the collection dimension never drifts
            values = (values + [0.0] * EMBED_DIM)[:EMBED_DIM]
        return values
    except Exception as e:
        print(f"[brand_memory] Gemini embedding error: {e}. Falling back to hashing embedding.")
        return None


# ---------------------------------------------------------------------------
# Deterministic hashing fallback (no API key required)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list:
    words = re.findall(r"\b[a-z']+\b", (text or "").lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def _hashing_embed(text: str) -> list:
    """
    Feature-hashing trick: each token votes (+1/-1, sign from a second
    hash) into one of EMBED_DIM buckets, then the vector is L2-normalized.
    Deterministic, offline, no model download — a reasonable stand-in for
    real embeddings when no API key is configured.
    """
    vector = [0.0] * EMBED_DIM
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        idx = h % EMBED_DIM
        sign = 1.0 if (h // EMBED_DIM) % 2 == 0 else -1.0
        vector[idx] += sign

    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector
