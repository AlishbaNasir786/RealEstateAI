"""
cache.py — In-Memory Cache for AI Marketing Chat Assistant
Caches generated content per (platform, objective, context signature)
to avoid duplicate AI calls for identical requests.
"""

import time
import json
import hashlib

CACHE_TTL_SECONDS = 3600 * 6  # 6 hours
_in_memory_cache = {}


def _make_key(platform: str, objective: str, context: dict) -> str:
    ctx_str = json.dumps(context or {}, sort_keys=True, default=str)
    digest = hashlib.md5(ctx_str.encode()).hexdigest()[:12]
    return f"{platform.lower()}:{objective.lower()}:{digest}"


def get_cached_content(platform: str, objective: str, context: dict):
    key = _make_key(platform, objective, context)
    entry = _in_memory_cache.get(key)
    if entry and (time.time() - entry["timestamp"]) < CACHE_TTL_SECONDS:
        return entry["content"]
    return None


def set_cached_content(platform: str, objective: str, context: dict, content: dict):
    key = _make_key(platform, objective, context)
    _in_memory_cache[key] = {
        "content": content,
        "timestamp": time.time(),
    }
