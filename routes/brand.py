"""
routes/brand.py — Blueprint for Brand Memory (RAG)
Provides REST API endpoints for managing the brand knowledge base and
asking brand-grounded questions against it.
"""

import sys
import os
import uuid
import tempfile

from flask import Blueprint, jsonify, request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.brand_memory import (
    init_brand_db, add_document, add_pdf_document, delete_document,
    list_documents, ask,
)

brand_bp = Blueprint('brand_bp', __name__)

# Ensure the local SQLite store + starter docs exist as soon as the
# blueprint is imported (mirrors init_auth_db() being called at startup).
init_brand_db()

MAX_PDF_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


@brand_bp.route('/api/brand/documents', methods=['GET'])
def api_list_documents():
    """Return all brand documents in the knowledge base (previews only)."""
    return jsonify({"success": True, "documents": list_documents()})


@brand_bp.route('/api/brand/documents', methods=['POST'])
def api_add_document():
    """
    Body (JSON): { "title": str, "content": str, "tags": str (optional) }
    """
    data = request.json or {}
    title = data.get('title')
    content = data.get('content')
    tags = data.get('tags', '')

    result = add_document(title, content, tags)
    status = 201 if result.get('success') else 400
    return jsonify(result), status


@brand_bp.route('/api/brand/documents/pdf', methods=['POST'])
def api_add_pdf_document():
    """
    Multipart form upload: file field 'file' (a .pdf), plus optional
    'title' and 'tags' form fields. Extracts text page-by-page, chunks it,
    embeds each chunk, and indexes it into the vector store.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'no file uploaded (expected field "file")'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'empty filename'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'only .pdf files are supported'}), 400

    title = request.form.get('title', '').strip() or os.path.splitext(file.filename)[0]
    tags = request.form.get('tags', '')

    tmp_path = os.path.join(tempfile.gettempdir(), f"brand_upload_{uuid.uuid4().hex}.pdf")
    try:
        file.save(tmp_path)
        if os.path.getsize(tmp_path) > MAX_PDF_SIZE_BYTES:
            return jsonify({'success': False, 'error': 'PDF exceeds 15MB limit'}), 400

        result = add_pdf_document(title, tmp_path, tags)
        status = 201 if result.get('success') else 400
        return jsonify(result), status
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@brand_bp.route('/api/brand/documents/<doc_id>', methods=['DELETE'])
def api_delete_document(doc_id):
    result = delete_document(doc_id)
    return jsonify(result), 200 if result.get('success') else 404


@brand_bp.route('/api/brand/ask', methods=['POST'])
def api_ask():
    """
    Body (JSON): { "question": str }
    Returns a brand-grounded answer plus the source documents used.
    """
    data = request.json or {}
    question = data.get('question')

    result = ask(question)
    status = 200 if result.get('success') else 400
    return jsonify(result), status
