"""
ad_generator.py — Multi-Platform Hyper-Personalized Ad Generator
Generates targeted ad variants for Meta, Google Search, WhatsApp, and LinkedIn
tailored to specific buyer personas. Headlines are market-standard and generic
(not tied to a specific property), following professional real-estate ad norms.
"""

import os
import json
import random
from datetime import datetime
from .segments import get_segment, SEGMENTS
from .cache import get_cached_ads, set_cached_ads


def generate_ad_campaign(segment_key: str, property_info: dict, force_refresh: bool = False) -> dict:
    """
    Main entry point for ad campaign generation.
    Checks cache first unless force_refresh is True.
    Uses Gemini LLM if API key exists, with automatic fallback to Rule Engine.
    """
    segment_key = segment_key.lower().strip()
    property_id = str(property_info.get("id") or property_info.get("title") or "custom_prop")

    if not force_refresh:
        cached = get_cached_ads(segment_key, property_id)
        if cached:
            cached["from_cache"] = True
            return cached

    # Attempt Gemini generation if API key is present
    campaign = _try_gemini_generation(segment_key, property_info)

    # Fallback to high-quality Rule Engine if Gemini is unavailable or fails
    if not campaign:
        campaign = _rule_based_ad_generation(segment_key, property_info)

    if campaign:
        set_cached_ads(segment_key, property_id, campaign)

    return campaign


def _rule_based_ad_generation(segment_key: str, prop: dict) -> dict:
    """
    Rule-based generator producing rich, structured multi-platform ad copy
    tailored specifically to the persona and property parameters.
    """
    seg = get_segment(segment_key)
    title = prop.get("title") or "Islamabad Property"
    location = prop.get("location") or prop.get("address") or "Islamabad"
    price = prop.get("price") or "Contact for Pricing"
    beds = prop.get("beds") or prop.get("bedrooms") or "3"
    baths = prop.get("baths") or prop.get("bathrooms") or "3"
    area = prop.get("area") or prop.get("size") or "1 Kanal"
    features = prop.get("features") or prop.get("amenities") or \
               ["Gated Community", "24/7 Security", "Prime Islamabad Location", "Modern Design"]
    if isinstance(features, str):
        features = [f.strip() for f in features.split(",")]

    feature_str = ", ".join(features[:4])

    meta_variant     = _generate_meta_variant(seg, title, location, price, beds, area, feature_str)
    google_variant   = _generate_google_variant(seg, title, location, price, beds)
    whatsapp_variant = _generate_whatsapp_variant(seg, title, location, price, beds, area, features)
    linkedin_variant = _generate_linkedin_variant(seg, title, location, price, area)

    return {
        "segment": seg,
        "property_summary": {
            "title": title,
            "location": location,
            "price": price,
            "beds": beds,
            "baths": baths,
            "area": area
        },
        "platforms": {
            "meta": meta_variant,
            "google": google_variant,
            "whatsapp": whatsapp_variant,
            "linkedin": linkedin_variant
        },
        "generated_by": "rule_engine",
        "generated_at": datetime.now().isoformat(),
        "from_cache": False
    }


# ─────────────────────────────────────────────────────────────────────────────
# PLATFORM GENERATORS — Market-Standard Generic Headlines
# ─────────────────────────────────────────────────────────────────────────────

def _generate_meta_variant(seg: dict, title: str, location: str, price: str,
                            beds: str, area: str, features: str) -> dict:
    key = seg["id"]

    if key == "family":
        headline = "Schools on Walking Distance · Parks · Gated Safety"
        primary_text = (
            "Your family deserves more than just a house — they deserve a community.\n\n"
            "Islamabad's top family-friendly sectors offer schools within walking distance, "
            "lush parks, 24/7 gated security, and spacious layouts designed for children to thrive.\n\n"
            "Trusted by 1,200+ families · Zero hidden charges · Site visits 7 days a week."
        )
        visual = "Children playing in a sun-filled park in front of a modern gated community"
        hook = "Live where your children's school is 5 minutes away — not 50."

    elif key == "investor":
        headline = "Prime Location · 9%+ Rental Yield · High Appreciation Zone"
        primary_text = (
            "Smart investors know: location beats luck every time.\n\n"
            "Islamabad's fastest-appreciating corridors are delivering 8–12% annual rental yields "
            "with strong tenant pipelines. Capital growth outperforms bank returns year-over-year.\n\n"
            "Data-backed picks · Fully tenanted options available · ROI reports on request."
        )
        visual = "Aerial drone shot of premium Islamabad real estate corridor with growth overlay"
        hook = "Your money should work harder than you do. Invest where yields are proven."

    elif key == "overseas":
        headline = "100% Verified · Remote Ownership · Virtual Tour Available"
        primary_text = (
            "Buying property in Pakistan from abroad just got effortless.\n\n"
            "Every listing is 100% NOC-verified with full legal title. "
            "Book via HD virtual walkthrough, transfer funds internationally, "
            "and receive possession papers — all without boarding a flight.\n\n"
            "Used by 3,000+ overseas Pakistanis · Dedicated remote support team · "
            "Free legal documentation check."
        )
        visual = "Overseas Pakistani family on video call touring their new Islamabad property virtually"
        hook = "Home is where your heart is — even when your passport is somewhere else."

    elif key == "luxury":
        headline = "Architectural Excellence · Smart Automation · VIP Sector Living"
        primary_text = (
            "Some properties are simply in a class of their own.\n\n"
            "Islamabad's ultra-premium sector residences feature imported Italian marble, "
            "full smart-home automation, panoramic Margalla Hills views, "
            "and concierge-level building management.\n\n"
            "Exclusive private showings by appointment · Strict buyer qualification · "
            "Collector-grade real estate."
        )
        visual = "Cinematic dusk shot of a modernist villa with pool terrace and Margalla Hills backdrop"
        hook = "Acquire the kind of property that appreciates in value and in prestige."

    elif key == "budget":
        headline = "Stop Renting — Own on Easy Monthly Installments"
        primary_text = (
            "Homeownership in Islamabad is closer than you think.\n\n"
            "Book with as little as 15% down and pay the balance over 3 years "
            "in manageable monthly installments — no bank loan required, no hidden fees.\n\n"
            "Possession handed at 50% payment · Verified developer · "
            "Limited units at this price — enquire today."
        )
        visual = "Happy young couple receiving house keys with a warm home exterior in background"
        hook = "The rent you pay monthly can build equity instead — starting today."

    else:  # tenant / young professional
        headline = "2 Min Walk to Metro · Fiber Internet · Vibrant Community"
        primary_text = (
            "Islamabad's most connected, walkable neighbourhoods are calling.\n\n"
            "Modern compact residences near F-7, F-11, and E-11 put the city's "
            "best cafes, co-working spaces, gyms, and transit links right at your doorstep.\n\n"
            "High-speed fiber in every unit · Low maintenance society · "
            "Flexible move-in timeline · Digital lease available."
        )
        visual = "Young professional working on laptop in a sleek modern apartment with cityscape view"
        hook = "Your commute should be counted in minutes, not hours."

    return {
        "headline": headline,
        "primary_text": primary_text,
        "cta": seg.get("primary_cta", "Enquire Now"),
        "visual_suggestion": visual,
        "target_hook": hook
    }


def _generate_google_variant(seg: dict, title: str, location: str,
                              price: str, beds: str) -> dict:
    key = seg["id"]

    if key == "family":
        h1 = "Family Homes Near Schools"
        h2 = "Gated Community · Safe Streets"
        h3 = "Parks & Playgrounds Nearby"
        d1 = "Find spacious family homes in Islamabad's safest gated sectors. Schools on walking distance."
        d2 = "Site visits 7 days a week. Zero hidden charges. Book your family tour today."

    elif key == "investor":
        h1 = "9%+ Yield Property Islamabad"
        h2 = "High Appreciation Corridor"
        h3 = "ROI Report Available Free"
        d1 = "Data-backed investment picks in Islamabad's fastest-growing sectors. Tenanted options."
        d2 = "Request full investor financial report. Capital growth outperforms fixed income returns."

    elif key == "overseas":
        h1 = "Buy Property from Abroad"
        h2 = "100% NOC Verified Listings"
        h3 = "Virtual HD Tours Available"
        d1 = "Seamless remote property purchase in Islamabad. Legal clearance, virtual tour, secure transfer."
        d2 = "Trusted by 3,000+ overseas Pakistanis. Free documentation review by our legal team."

    elif key == "luxury":
        h1 = "Ultra-Luxury Islamabad Homes"
        h2 = "Smart Home · VIP Sectors"
        h3 = "Private Showings By Appt."
        d1 = "Islamabad's most exclusive residences. Imported finishes, automation & Margalla Hills views."
        d2 = "Collector-grade real estate. Strict buyer qualification. Request private showing."

    elif key == "budget":
        h1 = "Homes on Installment Plan"
        h2 = "15% Down · Own in 3 Years"
        h3 = "No Bank Loan Needed"
        d1 = "Own your first home in Islamabad with 15% down. Monthly installments, no hidden charges."
        d2 = "Possession at 50% payment. Verified developer. Limited inventory — enquire today."

    else:
        h1 = "Modern Apartments Islamabad"
        h2 = "Metro · Fiber · Low Maintenance"
        h3 = "Walkable City Life"
        d1 = "Connected, affordable apartments near F-7, F-11, E-11. Metro access, fiber internet ready."
        d2 = "Flexible move-in. Digital lease. Perfect for young professionals and students."

    return {
        "headline_1": h1[:30],
        "headline_2": h2[:30],
        "headline_3": h3[:30],
        "description_1": d1[:90],
        "description_2": d2[:90],
        "sitelinks": [
            "Explore Properties",
            "View Sector Map",
            "Schedule Site Visit",
            "Payment Calculator"
        ]
    }


def _generate_whatsapp_variant(seg: dict, title: str, location: str, price: str,
                                beds: str, area: str, features: list) -> dict:
    feat_bullets = "\n".join([f"  • {f}" for f in features[:3]])

    message = (
        f"📢 *EXCLUSIVE REAL ESTATE UPDATE*\n\n"
        f"📍 *Location:* Islamabad\n"
        f"🏡 *Match:* {seg['label']} Listings Available\n\n"
        f"🌟 *Why These Properties Fit You:*\n"
        f"{feat_bullets}\n\n"
        f"👉 *{seg['hooks'][0]}*\n\n"
        f"💬 Reply *'YES'* or tap below to receive complete details & virtual tour instantly!"
    )

    return {
        "broadcast_message": message,
        "quick_reply_cta": "Chat on WhatsApp",
        "format": "Emoji-Rich Direct Broadcast"
    }


def _generate_linkedin_variant(seg: dict, title: str, location: str,
                                price: str, area: str) -> dict:
    post = (
        f"🏛️ *Real Estate Market Insights | Islamabad*\n\n"
        f"Islamabad remains Pakistan's most strategically positioned real estate market.\n\n"
        f"Key Drivers for {seg['label']}:\n"
        f"✔ High capital appreciation in top-tier sectors\n"
        f"✔ Premium rental demand and low vacancy rates\n"
        f"✔ Government-backed infrastructure expansion driving long-term value\n\n"
        f"Whether building institutional equity or long-term wealth assets, "
        f"Islamabad real estate remains Pakistan's premier inflation hedge.\n\n"
        f"📩 Request executive summary and market intelligence report."
    )

    return {
        "post_copy": post,
        "executive_headline": "Strategic Real Estate Opportunity — Islamabad",
        "cta_label": "Request Market Briefing"
    }


def _try_gemini_generation(segment_key: str, prop: dict) -> dict:
    """Attempt Gemini LLM generation if API key exists."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None

    try:
        import urllib.request
        seg = get_segment(segment_key)
        prompt = f"""You are a top-tier real estate advertising expert in Pakistan.
Generate hyper-personalized ad copy for target persona: {seg['label']} ({seg['tagline']}).
Property context: {json.dumps(prop)}

Use market-standard, generic professional headlines — not property-specific.
Examples: "Schools on Walking Distance", "9%+ Rental Yield", "100% NOC Verified"

Respond ONLY with valid JSON matching this schema:
{{
  "platforms": {{
    "meta": {{
      "headline": "string",
      "primary_text": "string",
      "cta": "string",
      "visual_suggestion": "string",
      "target_hook": "string"
    }},
    "google": {{
      "headline_1": "string (< 30 chars)",
      "headline_2": "string (< 30 chars)",
      "headline_3": "string (< 30 chars)",
      "description_1": "string (< 90 chars)",
      "description_2": "string (< 90 chars)",
      "sitelinks": ["string", "string", "string", "string"]
    }},
    "whatsapp": {{
      "broadcast_message": "string (with emojis)",
      "quick_reply_cta": "string",
      "format": "string"
    }},
    "linkedin": {{
      "post_copy": "string",
      "executive_headline": "string",
      "cta_label": "string"
    }}
  }}
}}
"""
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500}
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

        return {
            "segment": seg,
            "property_summary": prop,
            "platforms": data["platforms"],
            "generated_by": "gemini",
            "generated_at": datetime.now().isoformat(),
            "from_cache": False
        }
    except Exception as e:
        print(f"[ad_generator] Gemini API error: {e}. Falling back to Rule Engine.")
        return None
