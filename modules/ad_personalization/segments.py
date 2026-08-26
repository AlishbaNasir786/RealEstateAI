"""
segments.py — Customer Persona & Target Audience Definitions
Defines buyer segments, their key priorities, pain points, tone,
and marketing hooks for hyper-personalized real estate ad generation.
"""

SEGMENTS = {
    "family": {
        "id": "family",
        "label": "Family & Parent",
        "icon": "👨‍👩‍👧‍👦",
        "tagline": "Safety, Schools & Spacious Living",
        "general_tagline": "𝑰𝒔𝒍𝒂𝒎𝒂𝒃𝒂𝒅 𝒐𝒇𝒇𝒆𝒓𝒔 𝑰𝒔𝒍𝒂𝒎𝒂𝒃𝒂𝒅'𝒔 𝒔𝒂𝒇𝒆𝒔𝒕 𝒈𝒂𝒕𝒆𝒅 𝒄𝒐𝒎𝒎𝒖𝒏𝒊𝒕𝒊𝒆𝒔 𝒘𝒊𝒕𝒉 𝒕𝒐𝒑-𝒓𝒂𝒏𝒌𝒆𝒅 𝒔𝒄𝒉𝒐𝒐𝒍𝒔, 𝒍𝒖𝒔𝒉 𝒈𝒓𝒆𝒆𝒏 𝒑𝒂𝒓𝒌𝒔, 𝒂𝒏𝒅 𝒔𝒑𝒂𝒄𝒊𝒐𝒖𝒔 𝒇𝒂𝒎𝒊𝒍𝒚 𝒉𝒐𝒎𝒆𝒔 — 𝒈𝒊𝒗𝒊𝒏𝒈 𝒚𝒐𝒖𝒓 𝒄𝒉𝒊𝒍𝒅𝒓𝒆𝒏 𝒕𝒉𝒆 𝒔𝒆𝒄𝒖𝒓𝒆, 𝒕𝒉𝒓𝒊𝒗𝒊𝒏𝒈 𝒆𝒏𝒗𝒊𝒓𝒐𝒏𝒎𝒆𝒏𝒕 𝒕𝒉𝒆𝒚 𝒅𝒆𝒔𝒆𝒓𝒗𝒆.",
        "focus": ["Safety & Gated Security", "Nearby Top Schools", "Parks & Play Areas", "Spacious Bedrooms", "Family Neighborhood"],
        "pain_points": ["Safety concerns", "Long school commute for kids", "Cramped living space", "Lack of green parks"],
        "tone": "Warm, reassuring, practical, family-centric",
        "hooks": [
            "Give your children the neighborhood they deserve",
            "Safe gated living with top schools just 5 minutes away",
            "Spacious family home designed for lifelong memories"
        ],
        "primary_cta": "Schedule a Family Visit",
        "platforms": ["Meta (FB & IG)", "WhatsApp Broadcast", "Google Search"]
    },
    "investor": {
        "id": "investor",
        "label": "Investor & High ROI",
        "icon": "📈",
        "tagline": "Rental Yields, Capital Growth & Market Value",
        "general_tagline": "𝑰𝒔𝒍𝒂𝒎𝒂𝒃𝒂𝒅'𝒔 𝒑𝒓𝒆𝒎𝒊𝒖𝒎 𝒓𝒆𝒂𝒍 𝒆𝒔𝒕𝒂𝒕𝒆 𝒎𝒂𝒓𝒌𝒆𝒕 𝒅𝒆𝒍𝒊𝒗𝒆𝒓𝒔 8–12% 𝒂𝒏𝒏𝒖𝒂𝒍 𝒓𝒆𝒏𝒕𝒂𝒍 𝒚𝒊𝒆𝒍𝒅𝒔 𝒘𝒊𝒕𝒉 𝒄𝒐𝒏𝒔𝒊𝒔𝒕𝒆𝒏𝒕 𝒄𝒂𝒑𝒊𝒕𝒂𝒍 𝒂𝒑𝒑𝒓𝒆𝒄𝒊𝒂𝒕𝒊𝒐𝒏 — 𝒂 𝒅𝒂𝒕𝒂-𝒃𝒂𝒄𝒌𝒆𝒅, 𝒉𝒊𝒈𝒉-𝒈𝒓𝒐𝒘𝒕𝒉 𝒊𝒏𝒗𝒆𝒔𝒕𝒎𝒆𝒏𝒕 𝒐𝒑𝒑𝒐𝒓𝒕𝒖𝒏𝒊𝒕𝒚 𝒊𝒏 𝑷𝒂𝒌𝒊𝒔𝒕𝒂𝒏'𝒔 𝒎𝒐𝒔𝒕 𝒔𝒕𝒂𝒃𝒍𝒆 𝒄𝒊𝒕𝒚.",
        "focus": ["Rental Yield (8-12%)", "Capital Appreciation", "Price per Sq. Ft.", "High Demand Location", "Guaranteed Occupancy"],
        "pain_points": ["Low market transparency", "Low rental yields", "Unverified projects", "Slow appreciation"],
        "tone": "Confident, precise, data-driven, strategic",
        "hooks": [
            "Maximize your portfolio with up to 12% rental yield",
            "High-growth location poised for 25%+ appreciation",
            "Data-backed real estate asset in prime commercial belt"
        ],
        "primary_cta": "Request Investor Prospectus",
        "platforms": ["LinkedIn Professional", "Google Search", "Meta (FB & IG)"]
    },
    "overseas": {
        "id": "overseas",
        "label": "Overseas Pakistani",
        "icon": "✈️",
        "tagline": "100% Legal Verification, Trust & Virtual Tours",
        "general_tagline": "𝑶𝒘𝒏 𝒂 𝒇𝒖𝒍𝒍𝒚 𝒗𝒆𝒓𝒊𝒇𝒊𝒆𝒅, 𝑵𝑶𝑪-𝒄𝒍𝒆𝒂𝒓𝒆𝒅 𝒑𝒓𝒐𝒑𝒆𝒓𝒕𝒚 𝒊𝒏 𝑰𝒔𝒍𝒂𝒎𝒂𝒃𝒂𝒅 𝒇𝒓𝒐𝒎 𝒂𝒏𝒚𝒘𝒉𝒆𝒓𝒆 𝒊𝒏 𝒕𝒉𝒆 𝒘𝒐𝒓𝒍𝒅 — 𝒘𝒊𝒕𝒉 𝑯𝑫 𝒗𝒊𝒓𝒕𝒖𝒂𝒍 𝒕𝒐𝒖𝒓𝒔, 𝒄𝒐𝒎𝒑𝒍𝒆𝒕𝒆 𝒍𝒆𝒈𝒂𝒍 𝒕𝒓𝒂𝒏𝒔𝒑𝒂𝒓𝒆𝒏𝒄𝒚, 𝒂𝒏𝒅 𝒅𝒆𝒅𝒊𝒄𝒂𝒕𝒆𝒅 𝒓𝒆𝒎𝒐𝒕𝒆 𝒐𝒘𝒏𝒆𝒓𝒔𝒉𝒊𝒑 𝒔𝒖𝒑𝒑𝒐𝒓𝒕.",
        "focus": ["NOC / Legal Clearance", "Virtual Video Walkthroughs", "USD/PKR Exchange Advantage", "Property Management", "Secure Foreign Transfer"],
        "pain_points": ["Fear of property fraud", "Unable to physically visit", "Complicated documentation", "Management hassle"],
        "tone": "Trustworthy, transparent, patriotic, comforting",
        "hooks": [
            "Invest back home with 100% verified legal clearance",
            "Complete HD virtual tour & hassle-free remote ownership",
            "Leverage foreign currency strength for prime Pakistani real estate"
        ],
        "primary_cta": "Book HD Virtual Tour",
        "platforms": ["WhatsApp Broadcast", "Meta (FB & IG)", "Google Search"]
    },
    "luxury": {
        "id": "luxury",
        "label": "Luxury Seeker",
        "icon": "👑",
        "tagline": "Exclusivity, Smart Homes & Premium Amenities",
        "general_tagline": "𝑰𝒔𝒍𝒂𝒎𝒂𝒃𝒂𝒅'𝒔 𝒖𝒍𝒕𝒓𝒂-𝒑𝒓𝒆𝒎𝒊𝒖𝒎 𝒓𝒆𝒔𝒊𝒅𝒆𝒏𝒄𝒆𝒔 𝒓𝒆𝒅𝒆𝒇𝒊𝒏𝒆 𝒆𝒍𝒊𝒕𝒆 𝒍𝒊𝒗𝒊𝒏𝒈 — 𝒇𝒆𝒂𝒕𝒖𝒓𝒊𝒏𝒈 𝒔𝒎𝒂𝒓𝒕 𝒉𝒐𝒎𝒆 𝒂𝒖𝒕𝒐𝒎𝒂𝒕𝒊𝒐𝒏, 𝑰𝒕𝒂𝒍𝒊𝒂𝒏 𝒎𝒂𝒓𝒃𝒍𝒆 𝒊𝒏𝒕𝒆𝒓𝒊𝒐𝒓𝒔, 𝒑𝒓𝒊𝒗𝒂𝒕𝒆 𝒑𝒐𝒐𝒍𝒔, 𝒂𝒏𝒅 𝒑𝒂𝒏𝒐𝒓𝒂𝒎𝒊𝒄 𝑴𝒂𝒓𝒈𝒂𝒍𝒍𝒂 𝑯𝒊𝒍𝒍 𝒗𝒊𝒆𝒘𝒔 𝒊𝒏 𝒕𝒉𝒆 𝒎𝒐𝒔𝒕 𝒆𝒙𝒄𝒍𝒖𝒔𝒊𝒗𝒆 𝒔𝒆𝒄𝒕𝒐𝒓𝒔.",
        "focus": ["Private Pool / Penthouse", "Smart Home Automation", "Italian Marble & Designer Kitchens", "VIP Concierge & Valet", "Prime Sector Address"],
        "pain_points": ["Ordinary build quality", "Lack of exclusivity", "No privacy", "Standard fittings"],
        "tone": "Sophisticated, exclusive, refined, aspirational",
        "hooks": [
            "Experience uncompromised luxury in Islamabad's most coveted sector",
            "Architectural masterpiece equipped with full smart automation",
            "Private penthouse with panoramic skyline vistas"
        ],
        "primary_cta": "Request VIP Private Showing",
        "platforms": ["Instagram Showcase", "LinkedIn Professional", "Meta (FB & IG)"]
    },
    "budget": {
        "id": "budget",
        "label": "Budget & First-Time Buyer",
        "icon": "💡",
        "tagline": "Flexible Installment Plans & Affordable Ownership",
        "general_tagline": "𝑵𝒐𝒘 𝒊𝒏 𝑰𝒔𝒍𝒂𝒎𝒂𝒃𝒂𝒅, 𝒐𝒘𝒏𝒊𝒏𝒈 𝒚𝒐𝒖𝒓 𝒇𝒊𝒓𝒔𝒕 𝒉𝒐𝒎𝒆 𝒊𝒔 𝒆𝒂𝒔𝒊𝒆𝒓 𝒕𝒉𝒂𝒏 𝒆𝒗𝒆𝒓 — 𝒘𝒊𝒕𝒉 𝒋𝒖𝒔𝒕 10–15% 𝒅𝒐𝒘𝒏 𝒑𝒂𝒚𝒎𝒆𝒏𝒕, 𝒇𝒍𝒆𝒙𝒊𝒃𝒍𝒆 3-𝒚𝒆𝒂𝒓 𝒊𝒏𝒔𝒕𝒂𝒍𝒍𝒎𝒆𝒏𝒕 𝒑𝒍𝒂𝒏𝒔, 𝒛𝒆𝒓𝒐 𝒉𝒊𝒅𝒅𝒆𝒏 𝒄𝒉𝒂𝒓𝒈𝒆𝒔, 𝒂𝒏𝒅 𝒑𝒐𝒔𝒔𝒆𝒔𝒔𝒊𝒐𝒏 𝒔𝒕𝒂𝒓𝒕𝒊𝒏𝒈 𝒂𝒕 50% 𝒑𝒂𝒚𝒎𝒆𝒏𝒕. 𝑺𝒕𝒐𝒑 𝒓𝒆𝒏𝒕𝒊𝒏𝒈. 𝑺𝒕𝒂𝒓𝒕 𝒐𝒘𝒏𝒊𝒏𝒈.",
        "focus": ["Low Down Payment (10-15%)", "3-Year Easy Installment Plan", "Affordable Monthly EMI", "No Hidden Charges", "Possession on 50%"],
        "pain_points": ["High upfront capital requirement", "Hidden costs", "Unaffordable monthly plans", "Delayed possession"],
        "tone": "Encouraging, accessible, practical, value-oriented",
        "hooks": [
            "Own your dream home with just 15% down payment",
            "Stop paying rent — flexible 3-year easy installment plan available",
            "Affordable luxury made accessible for first-time buyers"
        ],
        "primary_cta": "Calculate Monthly Installment",
        "platforms": ["WhatsApp Broadcast", "Meta (FB & IG)", "Google Search"]
    },
    "tenant": {
        "id": "tenant",
        "label": "Young Professional / Student",
        "icon": "🎓",
        "tagline": "Proximity to Metro, Universities & Vibrant Hubs",
        "general_tagline": "𝑹𝒆𝒏𝒕 𝒂 𝒎𝒐𝒅𝒆𝒓𝒏, 𝒇𝒖𝒍𝒍𝒚-𝒇𝒖𝒓𝒏𝒊𝒔𝒉𝒆𝒅 𝒂𝒑𝒂𝒓𝒕𝒎𝒆𝒏𝒕 𝒊𝒏 𝑰𝒔𝒍𝒂𝒎𝒂𝒃𝒂𝒅 𝒂𝒕 𝒂𝒇𝒇𝒐𝒓𝒅𝒂𝒃𝒍𝒆 𝒑𝒓𝒊𝒄𝒆𝒔 — 𝒘𝒊𝒕𝒉 𝒖𝒏𝒊𝒏𝒕𝒆𝒓𝒓𝒖𝒑𝒕𝒆𝒅 𝒆𝒍𝒆𝒄𝒕𝒓𝒊𝒄𝒊𝒕𝒚, 𝒈𝒂𝒔, 𝒂𝒏𝒅 𝒘𝒂𝒕𝒆𝒓 𝒔𝒖𝒑𝒑𝒍𝒚, 𝒉𝒊𝒈𝒉-𝒔𝒑𝒆𝒆𝒅 𝒇𝒊𝒃𝒆𝒓 𝒊𝒏𝒕𝒆𝒓𝒏𝒆𝒕, 𝒂𝒏𝒅 𝒅𝒊𝒓𝒆𝒄𝒕 𝒂𝒄𝒄𝒆𝒔𝒔 𝒕𝒐 𝑴𝒆𝒕𝒓𝒐, 𝒖𝒏𝒊𝒗𝒆𝒓𝒔𝒊𝒕𝒊𝒆𝒔, 𝒂𝒏𝒅 𝒄𝒐𝒎𝒎𝒆𝒓𝒄𝒊𝒂𝒍 𝒉𝒖𝒃𝒔.",
        "focus": ["High-Speed Fiber Ready", "Near Metro & Bus Stops", "1-Bed / Studio Layout", "Vibrant Food & Shopping Street", "Low Maintenance Fee"],
        "pain_points": ["Long commute times", "Slow internet connectivity", "Overpriced rent", "High maintenance cost"],
        "tone": "Casual, energetic, modern, direct",
        "hooks": [
            "Modern studio apartment just 2 mins from Metro Station",
            "High-speed fiber-ready space tailored for young professionals",
            "Live in the center of food, shopping, and commercial hubs"
        ],
        "primary_cta": "Check Availability Now",
        "platforms": ["Meta (IG & FB)", "WhatsApp Broadcast"]
    }
}


def get_segment(segment_key: str) -> dict:
    """Return segment dictionary or default to 'family' if not found."""
    return SEGMENTS.get(segment_key.lower(), SEGMENTS["family"])


def get_all_segments() -> list:
    """Return list of all segments for UI display."""
    return list(SEGMENTS.values())
