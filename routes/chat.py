"""
routes/chat.py — Blueprint for the AI Marketing Chat Assistant
Provides REST API endpoints for listing platforms/objectives and
generating post titles, descriptions, hashtags, and email content.
"""

import sys
import os

from flask import Blueprint, jsonify, request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.chat_assistant import (
    get_all_platforms, get_all_objectives, generate_content,
)

chat_bp = Blueprint('chat_bp', __name__)

_saved_generations = []


@chat_bp.route('/api/chat/platforms', methods=['GET'])
def list_platforms():
    """Return all supported platforms with their format constraints."""
    return jsonify({"status": "success", "platforms": get_all_platforms()})


@chat_bp.route('/api/chat/objectives', methods=['GET'])
def list_objectives():
    """Return all supported marketing objectives."""
    return jsonify({"status": "success", "objectives": get_all_objectives()})


@chat_bp.route('/api/chat/generate', methods=['POST'])
def generate():
    """
    Body (JSON):
      {
        "platform":  str (required, e.g. "instagram"),
        "objective": str (required, e.g. "new_listing"),
        "context": {
            "topic": str, "location": str, "price": str,
            "highlights": [str, ...], "cta": str (all optional)
        }
      }
    """
    data = request.json or {}
    platform = data.get('platform')
    objective = data.get('objective')
    context = data.get('context') or {}

    if not platform:
        return jsonify({'success': False, 'error': 'platform is required'}), 400
    if not objective:
        return jsonify({'success': False, 'error': 'objective is required'}), 400

    result = generate_content(platform, objective, context)
    status = 200 if result.get('success') else 400
    return jsonify(result), status


@chat_bp.route('/api/chat/save', methods=['POST'])
def save_generation():
    """Body: the generated content dict to bookmark for later reuse."""
    data = request.json or {}
    if not data:
        return jsonify({'success': False, 'error': 'no content provided'}), 400
    _saved_generations.append(data)
    return jsonify({'success': True, 'total_saved': len(_saved_generations)}), 201


@chat_bp.route('/api/chat/saved', methods=['GET'])
def get_saved():
    return jsonify({'success': True, 'items': _saved_generations})
