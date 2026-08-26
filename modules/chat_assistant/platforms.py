"""
platforms.py — Platform & Objective Definitions
Defines the supported social/marketing platforms and campaign objectives
for the AI Marketing Chat Assistant, including format constraints
(char limits, hashtag counts) used by both the rule engine and the
Gemini prompt builder.
"""

PLATFORMS = {
    "facebook": {
        "id": "facebook",
        "label": "Facebook",
        "icon": "📘",
        "title_limit": 60,
        "description_limit": 400,
        "hashtag_count": 5,
        "tone": "Friendly, community-driven, benefit-led",
        "format_hint": "Short hook line, 2-3 sentence body, soft CTA at the end.",
    },
    "instagram": {
        "id": "instagram",
        "label": "Instagram",
        "icon": "📸",
        "title_limit": 50,
        "description_limit": 300,
        "hashtag_count": 12,
        "tone": "Visual-first, energetic, aspirational",
        "format_hint": "Punchy first line (before 'more'), emoji-friendly, hashtag block at the end.",
    },
    "linkedin": {
        "id": "linkedin",
        "label": "LinkedIn",
        "icon": "💼",
        "title_limit": 70,
        "description_limit": 600,
        "hashtag_count": 4,
        "tone": "Professional, data-driven, credible",
        "format_hint": "Lead with a market insight or stat, professional CTA, minimal emojis.",
    },
    "whatsapp": {
        "id": "whatsapp",
        "label": "WhatsApp",
        "icon": "💬",
        "title_limit": 40,
        "description_limit": 280,
        "hashtag_count": 0,
        "tone": "Direct, personal, urgent",
        "format_hint": "Feels like a message from a person, not an ad. Short, uses emojis sparingly, one clear CTA.",
    },
    "google": {
        "id": "google",
        "label": "Google Ads",
        "icon": "🔍",
        "title_limit": 30,
        "description_limit": 90,
        "hashtag_count": 0,
        "tone": "Clear, keyword-rich, action-oriented",
        "format_hint": "No emojis. Front-load the value proposition. Must fit strict character limits.",
    },
    "email": {
        "id": "email",
        "label": "Email",
        "icon": "📧",
        "title_limit": 78,
        "description_limit": 1200,
        "hashtag_count": 0,
        "tone": "Personable but polished, structured",
        "format_hint": "Subject line + short greeting + 2-3 short paragraphs + one clear CTA button text.",
    },
}

OBJECTIVES = {
    "lead_generation": {
        "id": "lead_generation",
        "label": "Lead Generation",
        "icon": "🎯",
        "goal": "Capture contact details or inquiries from interested prospects.",
        "cta_examples": ["Get a Free Consultation", "Request Details", "Book a Site Visit"],
    },
    "brand_awareness": {
        "id": "brand_awareness",
        "label": "Brand Awareness",
        "icon": "🌟",
        "goal": "Build recognition and trust in the brand without a hard sell.",
        "cta_examples": ["Learn More", "Follow Our Journey", "See Our Story"],
    },
    "new_listing": {
        "id": "new_listing",
        "label": "New Listing / Launch",
        "icon": "🏠",
        "goal": "Announce a new property, product, or service and drive interest fast.",
        "cta_examples": ["Book Your Viewing", "Reserve Now", "See the Listing"],
    },
    "promotion": {
        "id": "promotion",
        "label": "Promotion / Price Drop",
        "icon": "🏷️",
        "goal": "Highlight a limited-time offer, discount, or price change to drive urgency.",
        "cta_examples": ["Claim This Offer", "Limited Time — Act Now", "Grab the Deal"],
    },
    "engagement": {
        "id": "engagement",
        "label": "Engagement",
        "icon": "💬",
        "goal": "Spark comments, shares, or replies rather than direct conversion.",
        "cta_examples": ["Tell Us in the Comments", "Tag Someone Who Needs This", "Share Your Thoughts"],
    },
    "retargeting": {
        "id": "retargeting",
        "label": "Retargeting / Follow-up",
        "icon": "🔁",
        "goal": "Re-engage people who already showed interest but haven't converted yet.",
        "cta_examples": ["Still Interested? Let's Talk", "Pick Up Where You Left Off", "Your Match Is Still Available"],
    },
}


def get_platform(platform_id: str) -> dict:
    return PLATFORMS.get((platform_id or "").lower())


def get_objective(objective_id: str) -> dict:
    return OBJECTIVES.get((objective_id or "").lower())


def get_all_platforms() -> list:
    return list(PLATFORMS.values())


def get_all_objectives() -> list:
    return list(OBJECTIVES.values())
