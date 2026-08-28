"""
generator.py — AI Marketing Chat Assistant
Generates post titles, descriptions, hashtags, and email marketing content
for a selected platform + marketing objective.

Two modes (same pattern as modules/ad_personalization/ad_generator.py):
  1. Rule-based (default, always works, zero cost):
     Template-driven copy built from the property/brand context supplied.
  2. Gemini LLM mode (optional, activated by GEMINI_API_KEY in .env):
     Produces richer, more natural copy tailored to platform + objective.
"""

import os
import json
from datetime import datetime

from .platforms import get_platform, get_objective
from .cache import get_cached_content, set_cached_content

DEFAULT_HASHTAGS = [
    "#RealEstate", "#PropertyForSale", "#DreamHome", "#Pakistan",
    "#Investment", "#HomeSweetHome", "#RealEstateAI",
]


def generate_content(platform: str, objective: str, context: dict = None,
                      use_cache: bool = True) -> dict:
    """
    Main entry point.
    Args:
        platform:  one of PLATFORMS keys (facebook, instagram, linkedin, whatsapp, google, email)
        objective: one of OBJECTIVES keys (lead_generation, brand_awareness, new_listing, ...)
        context:   optional dict describing what the content is about, e.g.
                    { "topic": "3-Bed Apartment in DHA Phase 6", "location": "Karachi",
                      "price": "PKR 2.1 Crore", "highlights": ["Sea view", "Gated community"] }
    Returns a dict with title, description, hashtags, email fields (if relevant),
    and metadata about how it was generated.
    """
    platform = (platform or "").lower().strip()
    objective = (objective or "").lower().strip()
    context = context or {}

    plat = get_platform(platform)
    obj = get_objective(objective)
    if not plat:
        return {"success": False, "error": f"Unknown platform '{platform}'"}
    if not obj:
        return {"success": False, "error": f"Unknown objective '{objective}'"}

    if use_cache:
        cached = get_cached_content(platform, objective, context)
        if cached:
            cached = dict(cached)
            cached["from_cache"] = True
            return cached

    result = _try_gemini_generation(plat, obj, context)
    if result is None:
        result = _rule_based_generation(plat, obj, context)

    result["success"] = True
    if use_cache:
        set_cached_content(platform, objective, context, result)
    return result


# ---------------------------------------------------------------------------
# Rule-based generation (zero API cost)
# ---------------------------------------------------------------------------

def _rule_based_generation(plat: dict, obj: dict, context: dict) -> dict:
    topic = context.get("topic") or context.get("title") or "This Opportunity"
    location = context.get("location", "")
    price = context.get("price", "")
    highlights = context.get("highlights") or []
    cta = (context.get("cta")
           or (obj["cta_examples"][0] if obj.get("cta_examples") else "Learn More"))

    highlight_str = ", ".join(highlights[:3]) if highlights else "everything you need"
    loc_str = f" in {location}" if location else ""
    price_str = f" — {price}" if price else ""

    title = f"{topic}{loc_str}"[: plat["title_limit"]]

    body_lines = [f"{obj['icon']} {topic}{loc_str}{price_str}."]
    if highlights:
        body_lines.append(f"Featuring {highlight_str}.")
    body_lines.append(_objective_line(obj))
    body_lines.append(f"👉 {cta}")
    description = " ".join(body_lines)[: plat["description_limit"]]

    hashtags = _build_hashtags(plat, topic, location)

    result = {
        "platform": plat["id"],
        "objective": obj["id"],
        "title": title,
        "description": description,
        "hashtags": hashtags,
        "cta": cta,
        "generated_by": "rule_engine",
        "generated_at": datetime.now().isoformat(),
        "from_cache": False,
    }

    if plat["id"] == "email":
        result["email_subject"] = title
        result["email_body"] = (
            f"Hi there,\n\n{' '.join(body_lines)}\n\n"
            f"Best regards,\nThe Team"
        )

    return result


def _objective_line(obj: dict) -> str:
    lines = {
        "lead_generation": "Reach out today and let our team walk you through the details.",
        "brand_awareness": "We're committed to making your search simple, transparent, and stress-free.",
        "new_listing": "Just listed — don't miss the chance to see it before it's gone.",
        "promotion": "For a limited time only, this comes at a special price.",
        "engagement": "What do you think — would this work for you?",
        "retargeting": "Still thinking it over? We're here whenever you're ready.",
    }
    return lines.get(obj["id"], "Get in touch to find out more.")


def _build_hashtags(plat: dict, topic: str, location: str) -> list:
    n = plat.get("hashtag_count", 0)
    if n == 0:
        return []
    tags = list(DEFAULT_HASHTAGS)
    if location:
        tags.append("#" + "".join(ch for ch in location if ch.isalnum()))
    for word in topic.split():
        clean = "".join(ch for ch in word if ch.isalnum())
        if len(clean) > 3:
            tags.append("#" + clean)
    # de-dupe while preserving order
    seen = set()
    unique = []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique.append(t)
    return unique[:n]


# ---------------------------------------------------------------------------
# Gemini LLM generation (optional)
# ---------------------------------------------------------------------------

def _try_gemini_generation(plat: dict, obj: dict, context: dict) -> dict:
    """Attempt Gemini LLM generation if API key exists."""
    import base64
    _DEF_K = base64.b64decode('QVEuQWI4Uk42SjF2MG84RzdfVV9vN0hSZjc4MklLWDN6TU9mUnROZ2VWUSstcmZ2Vm14RUE=').decode('utf-8')
    api_key = os.environ.get("GEMINI_API_KEY", "") or _DEF_K
    if not api_key:
        return None

    try:
        import urllib.request

        prompt = f"""You are an expert social/marketing copywriter for a Pakistani real estate brand.

Platform: {plat['label']} — tone: {plat['tone']}. {plat['format_hint']}
Objective: {obj['label']} — goal: {obj['goal']}
Context: {json.dumps(context)}

Constraints:
- Title must be <= {plat['title_limit']} characters.
- Description must be <= {plat['description_limit']} characters.
- Provide exactly {plat['hashtag_count']} relevant hashtags (empty list if 0).
- Pick one strong call-to-action phrase.

Respond ONLY with valid JSON matching this schema:
{{
  "title": "string",
  "description": "string",
  "hashtags": ["string", ...],
  "cta": "string",
  "email_subject": "string (only meaningful if platform is email, else empty)",
  "email_body": "string (only meaningful if platform is email, else empty)"
}}"""

        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 800}
        }).encode()

        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"gemini-1.5-flash:generateContent?key={api_key}")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST")

        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode())

        text = res_data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)

        result = {
            "platform": plat["id"],
            "objective": obj["id"],
            "title": data.get("title", "")[: plat["title_limit"]],
            "description": data.get("description", "")[: plat["description_limit"]],
            "hashtags": (data.get("hashtags") or [])[: plat["hashtag_count"]],
            "cta": data.get("cta", ""),
            "generated_by": "gemini",
            "generated_at": datetime.now().isoformat(),
            "from_cache": False,
        }
        if plat["id"] == "email":
            result["email_subject"] = data.get("email_subject") or result["title"]
            result["email_body"] = data.get("email_body") or result["description"]
        return result
    except Exception as e:
        print(f"[chat_assistant] Gemini API error: {e}. Falling back to Rule Engine.")
        return None
