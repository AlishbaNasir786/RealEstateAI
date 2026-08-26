"""
cache.py — In-Memory & File Cache for Ad Generation
Caches generated ad campaigns per (segment, property_id) to eliminate duplicate AI calls.
"""

import time
import json
import os

CACHE_TTL_SECONDS = 86400 * 7  # 7 days
_in_memory_cache = {}


def _make_key(segment: str, property_id: str) -> str:
    return f"{segment.lower()}:{str(property_id).strip()}"


def get_cached_ads(segment: str, property_id: str):
    """Retrieve cached ad campaign if available and fresh."""
    key = _make_key(segment, property_id)
    entry = _in_memory_cache.get(key)
    if entry and (time.time() - entry["timestamp"]) < CACHE_TTL_SECONDS:
        return entry["campaign"]
    return None


def set_cached_ads(segment: str, property_id: str, campaign: dict):
    """Store generated ad campaign in cache."""
    key = _make_key(segment, property_id)
    _in_memory_cache[key] = {
        "campaign": campaign,
        "timestamp": time.time()
    }
