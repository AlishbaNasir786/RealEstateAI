"""
pdf_utils.py — PDF Extraction & Chunking
Extracts text from uploaded PDF brand documents and splits it into
overlapping chunks suitable for embedding + vector search.
"""

import re
from pypdf import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file, page by page, in reading order."""
    reader = PdfReader(file_path)
    pages_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages_text.append(text)
    return "\n\n".join(pages_text)


def chunk_text(text: str, chunk_size: int = 220, overlap: int = 40) -> list:
    """
    Split text into overlapping word-window chunks.
    chunk_size / overlap are measured in words — small enough that each
    chunk stays focused (better retrieval precision), with overlap so a
    fact split across a chunk boundary isn't lost entirely.
    """
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return []

    words = text.split(" ")
    if len(words) <= chunk_size:
        return [text]

    step = max(chunk_size - overlap, 1)
    chunks = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks
