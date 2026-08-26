"""
reviews.py — Reviews Collector
Reads customer reviews from Supabase `reviews` table.
Provides helpers for sentiment scoring, rating distribution,
and keyword extraction — all on data you own, zero external APIs needed.
"""

import sys
import os
import re
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import supabase


# ---------------------------------------------------------------------------
# Simple local sentiment scorer (no external API needed)
# ---------------------------------------------------------------------------

POSITIVE_WORDS = {
    "excellent", "great", "amazing", "wonderful", "fantastic", "love",
    "perfect", "brilliant", "outstanding", "superb", "satisfied", "happy",
    "impressed", "professional", "helpful", "fast", "easy", "smooth",
    "beautiful", "good", "best", "nice", "recommend", "trust", "reliable",
    "clean", "modern", "spacious", "responsive", "friendly", "prompt",
}

NEGATIVE_WORDS = {
    "bad", "poor", "terrible", "awful", "horrible", "worst", "hate",
    "slow", "rude", "unprofessional", "disappointed", "frustrating",
    "difficult", "problem", "issue", "broken", "dirty", "noisy", "late",
    "expensive", "overpriced", "misleading", "fake", "scam", "fraud",
    "unresponsive", "ignore", "ignored", "waste", "useless", "ugly",
}

NEGATION_WORDS = {
    "not", "no", "never", "n't", "isnt", "arent", "wasnt", "werent",
    "dont", "doesnt", "didnt", "cant", "couldnt", "without", "lack",
}


def _sentiment_score(text: str, rating: int = None) -> float:
    """
    Returns a sentiment score between -1.0 (very negative) and +1.0 (very positive).
    Uses rating as primary signal, with text negation & keyword matching as fallback.
    """
    if rating is not None:
        try:
            r = int(rating)
            if r <= 2:
                return -0.8
            if r >= 4:
                return 0.8
        except (ValueError, TypeError):
            pass

    if not text:
        return 0.0

    words = re.findall(r"\b[a-z']+\b", text.lower())
    pos = 0
    neg = 0

    for idx, w in enumerate(words):
        is_negated = False
        if idx > 0 and words[idx-1] in NEGATION_WORDS:
            is_negated = True
        elif idx > 1 and words[idx-2] in NEGATION_WORDS:
            is_negated = True

        if w in POSITIVE_WORDS:
            if is_negated:
                neg += 1
            else:
                pos += 1
        elif w in NEGATIVE_WORDS:
            if is_negated:
                pos += 1
            else:
                neg += 1

    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)


def _extract_keywords(text: str, top_n: int = 10) -> list:
    """Extract most frequent meaningful words from review text."""
    STOP = {
        "the", "a", "an", "is", "in", "it", "and", "to", "of", "for",
        "was", "are", "with", "this", "that", "my", "on", "be", "i",
        "we", "they", "he", "she", "our", "very", "so", "but", "at",
        "from", "by", "not", "have", "has", "had", "do", "did", "its",
    }
    words = re.findall(r"\b[a-z]{4,}\b", text.lower())
    freq = {}
    for w in words:
        if w not in STOP:
            freq[w] = freq.get(w, 0) + 1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_reviews(days: int = 90) -> list:
    """
    Fetch reviews from Supabase posted in the last `days` days.
    Returns list of review dicts with an added `sentiment` field.
    Schema: id, agent_id, user_id, rating, comment, created_at
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        res = supabase.table('reviews') \
            .select('id, agent_id, user_id, rating, comment, created_at') \
            .gte('created_at', since) \
            .order('created_at', desc=True) \
            .execute()
        reviews = res.data or []
    except Exception as e:
        print(f"[reviews] Supabase fetch error: {e}")
        reviews = []

    # Enrich with local sentiment + display name fallback
    for r in reviews:
        raw_comment = r.get('comment', '')
        name, clean_comment = _parse_name_from_comment(raw_comment)
        r['comment'] = clean_comment
        if not r.get('reviewer_name') or r.get('reviewer_name') == 'Anonymous' or str(r.get('reviewer_name')).startswith('User-'):
            r['reviewer_name'] = name
        r['sentiment'] = _sentiment_score(clean_comment, rating=r.get('rating'))

    return reviews


def get_all_reviews() -> list:
    """Fetch every review ever submitted (no date filter)."""
    try:
        res = supabase.table('reviews') \
            .select('id, agent_id, user_id, rating, comment, created_at') \
            .order('created_at', desc=True) \
            .execute()
        reviews = res.data or []
    except Exception as e:
        print(f"[reviews] Supabase fetch error: {e}")
        reviews = []

    for r in reviews:
        raw_comment = r.get('comment', '')
        name, clean_comment = _parse_name_from_comment(raw_comment)
        r['comment'] = clean_comment
        if not r.get('reviewer_name') or r.get('reviewer_name') == 'Anonymous' or str(r.get('reviewer_name')).startswith('User-'):
            r['reviewer_name'] = name
        r['sentiment'] = _sentiment_score(clean_comment, rating=r.get('rating'))

    return reviews


def submit_review(reviewer_name: str, rating: int, comment: str,
                  source: str = 'website', property_id: str = None) -> dict:
    """
    Insert a new review into the Supabase `reviews` table.
    Actual schema: id, agent_id, user_id, rating, comment, created_at
    reviewer_name is stored in the comment prefix since no dedicated column exists.
    Returns the inserted record or an error dict.
    """
    rating = max(1, min(5, int(rating)))
    name   = reviewer_name.strip()[:80]
    body   = comment.strip()[:1900]
    # Store name inline in comment as "[Name]: comment" since schema has no name col
    full_comment = f"[{name}]: {body}"

    payload = {
        "rating":  rating,
        "comment": full_comment,
    }

    try:
        res = supabase.table('reviews').insert(payload).execute()
        inserted = res.data[0] if res.data else {}
        # Parse name back out for the response
        inserted['reviewer_name'] = name
        return {"success": True, "data": inserted}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_name_from_comment(comment: str) -> tuple:
    """
    Parses '[Name]: actual comment' format.
    Returns (name, clean_comment).
    """
    import re
    m = re.match(r'^\[([^\]]{1,80})\]:\s*(.*)', comment or '', re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return 'Anonymous', comment or ''


def compute_review_stats(reviews: list) -> dict:
    """
    Compute aggregated statistics from a list of review dicts.
    Returns a dict safe to pass directly to the insights engine.
    """
    if not reviews:
        return {
            "total": 0, "avg_rating": 0.0, "distribution": {},
            "avg_sentiment": 0.0, "top_keywords": [],
            "recent_comments": [], "complaints": [], "praises": [],
        }

    total    = len(reviews)
    ratings  = [r.get("rating", 3) for r in reviews]
    avg_r    = round(sum(ratings) / total, 2)
    dist     = {str(i): ratings.count(i) for i in range(1, 6)}

    sentiments = [r.get("sentiment", 0.0) for r in reviews]
    avg_sent   = round(sum(sentiments) / total, 3)

    # Extract clean comment text (strip [Name]: prefix)
    clean_comments = []
    for r in reviews:
        raw = r.get('comment', '')
        name, clean = _parse_name_from_comment(raw)
        if not r.get('reviewer_name') or r['reviewer_name'] == 'Anonymous':
            r['reviewer_name'] = name
        r['clean_comment'] = clean
        clean_comments.append(clean)

    all_text   = ' '.join(clean_comments)
    keywords   = _extract_keywords(all_text, top_n=15)

    complaints = [
        r.get('clean_comment', r.get('comment', ''))[:200]
        for r in reviews if r.get('rating', 3) <= 2
    ][:10]

    praises = [
        r.get('clean_comment', r.get('comment', ''))[:200]
        for r in reviews if r.get('rating', 5) >= 4
    ][:10]

    recent = [
        {
            "name":    r.get("reviewer_name", "Anonymous"),
            "rating":  r.get("rating", 3),
            "comment": r.get('clean_comment', r.get('comment', ''))[:300],
            "date":    r.get("created_at", "")[:10],
        }
        for r in reviews[:8]
    ]

    return {
        "total":           total,
        "avg_rating":      avg_r,
        "distribution":    dist,
        "avg_sentiment":   avg_sent,
        "top_keywords":    keywords,
        "recent_comments": recent,
        "complaints":      complaints,
        "praises":         praises,
    }
