"""
aggregator.py — Data Aggregator
Merges review stats + website scan results into one unified dataset
that the insights engine consumes.

Design rule: this file has ZERO AI calls — it only merges data.
All intelligence lives in insights_engine.py.
"""

from .reviews import get_reviews, compute_review_stats
from .website_scanner import scan_website


def run_full_analysis(scan_days: int = 90, pages: list = None) -> dict:
    """
    Runs both collectors and returns a single merged payload dict.

    Args:
        scan_days: How many days of reviews to include.
        pages:     Optional override for pages to scan (defaults to PAGES_TO_SCAN).

    Returns:
        {
          "reviews":  { ...review stats... },
          "website":  { ...scan results... },
          "summary":  { ...cross-signal highlights... }
        }
    """
    print("[aggregator] Fetching reviews…")
    reviews      = get_reviews(days=scan_days)
    review_stats = compute_review_stats(reviews)

    print("[aggregator] Scanning website…")
    website_data = scan_website(pages=pages)

    # Cross-signal: find pages that correlate with complaints
    # e.g. if reviews mention "hard to find" → flag nav/UX pages
    complaint_text = " ".join(review_stats.get("complaints", [])).lower()
    cross_signals  = []

    if any(kw in complaint_text for kw in ["slow", "load", "wait", "speed"]):
        cross_signals.append({
            "type":    "performance",
            "message": "Reviews mention slow loading — correlates with scanner's load time metrics",
        })
    if any(kw in complaint_text for kw in ["find", "search", "navigate", "confusing", "lost"]):
        cross_signals.append({
            "type":    "ux",
            "message": "Reviews mention navigation difficulty — review site structure and labelling",
        })
    if any(kw in complaint_text for kw in ["image", "photo", "picture", "blurry", "dark"]):
        cross_signals.append({
            "type":    "content",
            "message": "Reviews complain about images — correlates with missing alt-text scanner findings",
        })
    if any(kw in complaint_text for kw in ["price", "cost", "expensive", "value"]):
        cross_signals.append({
            "type":    "pricing",
            "message": "Reviews mention pricing concerns — consider adding clearer pricing breakdowns",
        })
    if any(kw in complaint_text for kw in ["contact", "respond", "reply", "callback"]):
        cross_signals.append({
            "type":    "communication",
            "message": "Reviews flag contact/response issues — check if contact forms and WhatsApp links are prominent",
        })

    summary = {
        "review_count":        review_stats["total"],
        "avg_rating":          review_stats["avg_rating"],
        "total_site_issues":   website_data["total_issues"],
        "avg_load_time_ms":    website_data.get("avg_load_time_ms"),
        "cross_signals":       cross_signals,
        "overall_health":      _compute_health_score(review_stats, website_data),
    }

    return {
        "reviews": review_stats,
        "website": website_data,
        "summary": summary,
    }


def _compute_health_score(review_stats: dict, website_data: dict) -> dict:
    """
    Computes a simple 0–100 health score for each dimension.
    Used by the frontend to render score rings.
    """
    # Review health (0–100): based on avg rating (1–5 scale → 0–100)
    avg_r = review_stats.get("avg_rating", 0)
    review_health = round((avg_r / 5) * 100, 1)

    # SEO health: penalise for each missing meta/title/h1 issue
    seo_issues = sum(
        1
        for issue_dict in website_data.get("all_issues", [])
        if any(k in issue_dict.get("issue", "").lower()
               for k in ["meta", "title", "h1", "alt", "heading", "canonical"])
    )
    seo_health = max(0, round(100 - (seo_issues * 12), 1))

    # Performance health: based on avg load time
    avg_load = website_data.get("avg_load_time_ms") or 500
    if avg_load < 500:
        perf_health = 100
    elif avg_load < 1000:
        perf_health = 80
    elif avg_load < 2000:
        perf_health = 55
    else:
        perf_health = 30

    # Content health: penalise for thin content / missing images alt / missing inventory photos & descriptions
    content_issues = sum(
        1
        for issue_dict in website_data.get("all_issues", [])
        if any(k in issue_dict.get("issue", "").lower()
               for k in ["content", "word", "image", "alt", "paragraph"])
    )
    content_health = max(0, round(100 - (content_issues * 10), 1))

    inventory = website_data.get("inventory", {})
    tot_listings = inventory.get("total_listings", 0)
    if tot_listings > 0:
        missing_imgs = inventory.get("missing_images", 0)
        missing_descs = inventory.get("missing_description", 0)
        img_pen = (missing_imgs / tot_listings) * 25
        desc_pen = (missing_descs / tot_listings) * 15
        content_health = max(0, round(content_health - img_pen - desc_pen, 1))

    overall = round(
        (review_health * 0.35 + seo_health * 0.25 + perf_health * 0.20 + content_health * 0.20),
        1,
    )

    return {
        "overall":     overall,
        "reviews":     review_health,
        "seo":         seo_health,
        "performance": perf_health,
        "content":     content_health,
    }

