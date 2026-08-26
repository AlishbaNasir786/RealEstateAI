"""
insights_engine.py — AI Insights Engine
Converts the merged review + website data into structured, actionable
recommendations.

Two modes:
  1. Rule-based (default, always works, zero cost):
     Pattern-matches thresholds and known issue signatures to produce
     recommendations — same approach used by the competitor engine.

  2. Gemini LLM mode (optional, activated by GEMINI_API_KEY in .env):
     Passes the aggregated data to Google Gemini and forces structured
     JSON output for richer, more nuanced suggestions.
"""

import os
import json
import re
from datetime import datetime


# ---------------------------------------------------------------------------
# Severity + priority constants
# ---------------------------------------------------------------------------

HIGH   = "high"
MEDIUM = "medium"
LOW    = "low"


# ---------------------------------------------------------------------------
# Rule-based insights (zero API cost)
# ---------------------------------------------------------------------------

def _rule_based_insights(data: dict) -> dict:
    """
    Generates structured AI insights and weak points purely based on
    customer reviews, star ratings, comments, and property likes.
    """
    reviews    = data.get("reviews", {})
    engagement = data.get("engagement", {})

    weak_points     = []
    recommendations = []
    strengths       = []

    avg_rating   = float(reviews.get("avg_rating", 0.0))
    total_reviews= int(reviews.get("total", 0))
    avg_sentiment= float(reviews.get("avg_sentiment", 0.0))
    complaints   = reviews.get("complaints", [])
    praises      = reviews.get("praises", [])
    dist         = reviews.get("distribution", {})
    
    total_likes  = int(engagement.get("total_likes", 0))
    total_prop_rev = int(engagement.get("total_listing_reviews", 0))
    top_liked    = engagement.get("top_liked_listings", [])
    per_prop     = engagement.get("per_property_stats", [])

    # 1. Total Reviews & Rating Evaluation
    if total_reviews == 0:
        weak_points.append({
            "category": "Customer Reviews",
            "severity": HIGH,
            "issue":    "Zero Customer Reviews Logged",
            "detail":   "The platform currently has 0 customer reviews recorded in the database.",
            "action":   "Prompt satisfied buyers via automated WhatsApp follow-ups after property viewings.",
            "impact":   "Verified customer reviews increase buyer conversion by up to 270%.",
        })
    elif avg_rating < 3.8:
        low_stars = int(dist.get("1", 0)) + int(dist.get("2", 0))
        weak_points.append({
            "category": "Customer Satisfaction",
            "severity": HIGH if avg_rating < 3.2 else MEDIUM,
            "issue":    f"Below-Target Average Rating ({avg_rating:.2f} / 5.0)",
            "detail":   f"Based on {total_reviews} reviews with {low_stars} critical 1★ & 2★ ratings." + (f" Key complaints: {'; '.join(complaints[:2])}" if complaints else ""),
            "action":   "Address specific service issues mentioned in low-star reviews and follow up with dissatisfied clients.",
            "impact":   "Achieving a 4.2+ rating significantly boosts organic buyer inquiries.",
        })
    else:
        strengths.append(f"High customer satisfaction: {avg_rating:.2f} / 5.0 across {total_reviews} verified reviews.")

    # 2. Review Sentiment Analysis
    if total_reviews > 0 and avg_sentiment < 0:
        weak_points.append({
            "category": "Review Sentiment",
            "severity": HIGH,
            "issue":    f"Negative Sentiment Score ({avg_sentiment:.2f})",
            "detail":   "Negative emotional tone detected in customer comments.",
            "action":   "Audit recent client conversations and implement quality control for agent interactions.",
            "impact":   "Positive sentiment directly increases lead closing rates.",
        })
    elif avg_sentiment > 0.3 and total_reviews > 0:
        strengths.append(f"Positive client sentiment ({avg_sentiment:.2f}) across recent review text.")

    # 3. Property Likes & Engagement Evaluation
    if total_likes == 0:
        weak_points.append({
            "category": "Property Engagement",
            "severity": MEDIUM,
            "issue":    "Zero Heart/Like Engagement on Property Listings",
            "detail":   "No property listings have received user hearts/likes yet.",
            "action":   "Add prominent 'Save / Like Property' buttons and highlight trending properties.",
            "impact":   "Listing engagement builds buyer interest and repeat website visits.",
        })
    elif total_likes < 5:
        weak_points.append({
            "category": "Property Engagement",
            "severity": LOW,
            "issue":    f"Low Property Like Count ({total_likes} Total Likes)",
            "detail":   f"Only {total_likes} property likes registered across the active inventory.",
            "action":   "Feature most-liked properties on the home banner to encourage buyer interactions.",
            "impact":   "Higher like engagement improves property visibility.",
        })
    else:
        strengths.append(f"Active buyer engagement: {total_likes} total property likes recorded.")

    # 4. Listing-Specific Reviews Evaluation
    if total_prop_rev == 0 and total_reviews > 0:
        weak_points.append({
            "category": "Listing Feedback",
            "severity": LOW,
            "issue":    "No Specific Property Listing Reviews",
            "detail":   "Reviews are general platform feedback rather than property-specific reviews.",
            "action":   "Add a direct review widget on property detail pages for specific listings.",
            "impact":   "Property-specific reviews improve trust for individual listings.",
        })

    # ── Dynamic Recommendations ───────────────────────────────────────────────
    if avg_rating < 4.0:
        recommendations.append(f"Improve overall rating from {avg_rating:.2f} to 4.2+ by resolving common customer complaints.")
    else:
        recommendations.append(f"Prominently display your {avg_rating:.2f}/5.0 star rating on property listing headers as social proof.")

    if total_likes < 10:
        recommendations.append(f"Encourage buyers to heart/save listings to increase the current total of {total_likes} property likes.")
    else:
        recommendations.append(f"Create a 'Most Popular Listings' carousel using your top-liked properties ({total_likes} total likes).")

    if total_reviews < 15:
        recommendations.append(f"Expand review collection from current {total_reviews} reviews to 25+ via automated post-viewing WhatsApp prompts.")

    if praises:
        strengths.append(f"Buyers praise: '{praises[0]}'")

    return {
        "weak_points":     weak_points,
        "recommendations": recommendations,
        "strengths":       strengths,
    }

    return {
        "weak_points":      weak_points,
        "recommendations":  recommendations[:8],
        "strengths":        strengths[:5],
        "generated_by":     "rule_engine",
        "generated_at":     datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Gemini LLM mode (optional)
# ---------------------------------------------------------------------------

def _gemini_insights(data: dict) -> dict:
    """
    Calls the Google Gemini API with the aggregated data to generate
    richer insights. Falls back to rule-based on any failure.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None

    try:
        import urllib.request

        # Prepare a concise summary payload (trim to keep tokens low)
        reviews = data.get("reviews", {})
        website = data.get("website", {})
        payload_summary = {
            "avg_rating":       reviews.get("avg_rating"),
            "total_reviews":    reviews.get("total"),
            "avg_sentiment":    reviews.get("avg_sentiment"),
            "top_keywords":     reviews.get("top_keywords", [])[:10],
            "complaints":       reviews.get("complaints", [])[:5],
            "praises":          reviews.get("praises", [])[:3],
            "total_site_issues":website.get("total_issues"),
            "avg_load_ms":      website.get("avg_load_time_ms"),
            "images_missing_alt":website.get("images_missing_alt"),
            "pages_without_meta":website.get("pages_without_meta"),
            "site_issues_sample":[d.get("issue") for d in website.get("all_issues", [])[:8]],
        }

        prompt = f"""You are a senior real estate business consultant analyzing a Pakistani property platform for its owner.

Here is the aggregated performance & review data:
{json.dumps(payload_summary, indent=2)}

Analyse this data and respond ONLY with valid JSON matching exactly this schema:
{{
  "weak_points": [
    {{
      "category": "string (business area e.g. Customer Satisfaction, Search Visibility, User Experience)",
      "severity": "high|medium|low",
      "issue": "string (owner-friendly description, < 80 chars)",
      "detail": "string (clear business explanation, < 200 chars)",
      "action": "string (practical business advice/fix, < 150 chars)",
      "impact": "string (expected business outcome, < 100 chars)"
    }}
  ],
  "recommendations": ["string (business action item)", "string", "string"],
  "strengths": ["string (business strength)"],
  "generated_by": "gemini"
}}

Rules:
- Write for a real estate business owner, NOT a technical web developer. Avoid jargon like 'H1 tags', 'alt text', 'meta descriptions'. Use 'Page Headline', 'Image Search Labels', 'Google Search Summary' instead.
- weak_points: list 4–8 items, most critical business issues first
- recommendations: list 5–7 practical business recommendations
- strengths: list 2–4 genuine business achievements
- Do NOT include markdown, explanation, or text outside the JSON object.
"""

        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500}
        }).encode()

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={api_key}"
        )
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        raw_text = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        # Strip any markdown code fences
        raw_text = re.sub(r"```(?:json)?", "", raw_text).strip()
        parsed = json.loads(raw_text)
        parsed["generated_at"] = datetime.now().isoformat()
        return parsed

    except Exception as e:
        print(f"[insights] Gemini call failed: {e} — falling back to rule engine")
        return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_insights(data: dict) -> dict:
    """
    Main entry point — tries Gemini first, falls back to rule-based engine.
    `data` is the dict returned by aggregator.run_full_analysis().
    """
    gemini_result = _gemini_insights(data)
    if gemini_result:
        return gemini_result
    return _rule_based_insights(data)
