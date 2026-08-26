"""
Persona Engine & WhatsApp Generator Module
Provides Python programmatic interface for buyer persona profiling,
platform suitability ranking, inventory matching from scraped CSVs,
and WhatsApp marketing message generation.
"""

import os
import sys
import io
import re
import csv
import random
import urllib.parse
from datetime import datetime

# Force UTF-8 output so emoji print correctly on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")



# ---------------------------------------------------------------------------
# Persona Configurations & Platform Matrix
# ---------------------------------------------------------------------------

PERSONA_PROFILES = {
    "investor": {
        "title": "Yield & Growth Capitalist",
        "badge": "Investor Archetype",
        "description": "High focus on rental ROI, capital appreciation potential, and pre-launch prices.",
        "angle": "Highlights ROI calculation, rental yield projections, and pre-launch pricing urgency.",
        "hook": "📈 *HIGH-YIELD REAL ESTATE INVESTMENT OPPORTUNITY* 📈",
        "platforms": [
            {"name": "WhatsApp Direct Broadcast", "score": 96, "color": "#25d366"},
            {"name": "LinkedIn Professional Network", "score": 84, "color": "#0077b5"},
            {"name": "Direct Portal Alerts", "score": 78, "color": "#38bdf8"},
            {"name": "Email Investment Digest", "score": 65, "color": "#f59e0b"},
        ]
    },
    "first_time": {
        "title": "Security & First-Home Seeker",
        "badge": "First Buyer Archetype",
        "description": "Prioritizes easy installment plans, builder reputation, and immediate possession.",
        "angle": "Highlights installment breakdown, clear title verification, and family safety.",
        "hook": "🔑 *AFFORDABLE FIRST-HOME OPPORTUNITY* 🔑",
        "platforms": [
            {"name": "Instagram & Reels Showcase", "score": 92, "color": "#e1306c"},
            {"name": "WhatsApp Advisory Chat", "score": 88, "color": "#25d366"},
            {"name": "Direct Web Search Portal", "score": 85, "color": "#38bdf8"},
            {"name": "Facebook Community Groups", "score": 74, "color": "#1877f2"},
        ]
    },
    "family": {
        "title": "Family Nest & Space Upgrader",
        "badge": "Family Archetype",
        "description": "Seeking 3-5 bedrooms, gated security, nearby top schools, and green parks.",
        "angle": "Emphasizes neighbourhood tranquility, bedroom count, and proximity to schools.",
        "hook": "🏡 *SPACIOUS FAMILY HOME SPOTLIGHT* 🏡",
        "platforms": [
            {"name": "WhatsApp Video Walkthrough", "score": 94, "color": "#25d366"},
            {"name": "Facebook Meta Ads", "score": 86, "color": "#1877f2"},
            {"name": "Direct Portal Search", "score": 82, "color": "#38bdf8"},
            {"name": "Community Email Newsletter", "score": 68, "color": "#f59e0b"},
        ]
    },
    "luxury": {
        "title": "Executive Portfolio Collector",
        "badge": "Luxury Archetype",
        "description": "Demands prime boulevard location, modern architectural aesthetics, and privacy.",
        "angle": "Conveys exclusive white-glove availability, prime location prestige, and luxury finishes.",
        "hook": "💎 *PREMIUM LUXURY RESIDENCE SPOTLIGHT* 💎",
        "platforms": [
            {"name": "Private WhatsApp VIP Concierge", "score": 98, "color": "#25d366"},
            {"name": "LinkedIn Executive Network", "score": 90, "color": "#0077b5"},
            {"name": "Instagram High-Design Feed", "score": 85, "color": "#e1306c"},
            {"name": "Bespoke Portfolio Mailer", "score": 72, "color": "#f59e0b"},
        ]
    }
}

VERIFIED_AGENTS = [
    {"name": "Tariq Mahmood", "title": "Senior Investment Advisor", "agency": "Premier Real Estate", "phone": "+923005551234"},
    {"name": "Zainab Chaudhry", "title": "Residential Specialist", "agency": "Apex Luxury Properties", "phone": "+923219876543"},
    {"name": "Bilal Farooq", "title": "Commercial Portfolio Manager", "agency": "Capital Heights Realty", "phone": "+923334445566"},
    {"name": "Hamza Alvi", "title": "Property Consultant", "agency": "Zameen Platinum Partners", "phone": "+923451122334"}
]

FALLBACK_LISTINGS = [
    {
        "title": "10 Marla Brand New Modern House in G-13",
        "city": "Houses_Islamabad",
        "listing_mode": "for_sale",
        "property_type": "House",
        "price": "PKR 2.85 Crore",
        "price_numeric": 28500000,
        "beds": 5, "baths": 6, "area": "10 Marla"
    },
    {
        "title": "1 Kanal Luxury Executive Villa in DHA Phase 2",
        "city": "Houses_Islamabad",
        "listing_mode": "for_sale",
        "property_type": "House",
        "price": "PKR 6.5 Crore",
        "price_numeric": 65000000,
        "beds": 6, "baths": 7, "area": "1 Kanal"
    },
    {
        "title": "3 Bed Luxury Apartment in E-11 Sector",
        "city": "Flats_Rent_Islamabad",
        "listing_mode": "for_rent",
        "property_type": "Flat",
        "price": "PKR 110 Thousand",
        "price_numeric": 110000,
        "beds": 3, "baths": 3, "area": "2100 Sq Ft"
    },
    {
        "title": "5 Marla Stylish House in Bahria Town Sector C",
        "city": "Houses_Lahore",
        "listing_mode": "for_sale",
        "property_type": "House",
        "price": "PKR 1.85 Crore",
        "price_numeric": 18500000,
        "beds": 3, "baths": 4, "area": "5 Marla"
    }
]

# ---------------------------------------------------------------------------
# Core Engine Functions
# ---------------------------------------------------------------------------

# Add path for importing db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import supabase

def load_inventory_csv(filepath: str = "data/zameen_all_listings.csv") -> list:
    """Load inventory listings from Supabase (formerly from CSV) or return fallback data on failure."""
    try:
        response = supabase.table('properties').select('*, property_images(*), agents(*), cities(*)').execute()
        listings = response.data
        if not listings:
            return FALLBACK_LISTINGS
            
        # Clean up database row structures to match what the engine expects
        for row in listings:
            # Flatten city
            if isinstance(row.get("cities"), dict) and "name" in row["cities"]:
                row["city"] = row["cities"]["name"]
                
            # Ensure price_numeric exists
            try:
                row["price_numeric"] = int(float(row.get("price_numeric") or row.get("price") or 0))
            except (ValueError, TypeError):
                row["price_numeric"] = 0
                
            # Map listing_purpose to listing_mode
            if "listing_purpose" in row:
                purpose = row["listing_purpose"]
                row["listing_mode"] = "for_sale" if purpose == "buy" else "for_rent" if purpose == "rent" else purpose
                
        return listings
    except Exception as e:
        print(f"Warning loading from Supabase: {e}")
        return FALLBACK_LISTINGS


def match_listings(listings: list, city: str = "Islamabad", mode: str = "for_sale", prop_type: str = None) -> list:
    """Filter listings strictly by city, mode (sale/rent), and optional property type."""
    city_clean = city.lower()
    mode_clean = mode.lower()
    
    # 1. Strict match: City + Mode + Property Type
    matches = []
    for item in listings:
        item_city = str(item.get("city", "")).lower()
        item_mode = str(item.get("listing_mode", "")).lower()
        item_type = str(item.get("property_type", "")).lower()

        if city_clean in item_city and mode_clean in item_mode:
            if prop_type and prop_type.lower() not in item_type:
                continue
            matches.append(item)

    # 2. Strict City + Mode match (ignoring prop_type)
    if not matches:
        matches = [l for l in listings if city_clean in str(l.get("city", "")).lower() and mode_clean in str(l.get("listing_mode", "")).lower()]

    # 3. Strict City-only match (never cross city boundaries)
    if not matches:
        matches = [l for l in listings if city_clean in str(l.get("city", "")).lower()]

    # 4. Safe fallback: clean city-specific template if 0 listings exist for this city
    if not matches:
        matches = [{
            "title": f"Prime {prop_type or 'Property'} Opportunity in {city}",
            "city": f"{prop_type or 'Houses'}_{city}",
            "listing_mode": mode,
            "property_type": prop_type or "House",
            "price": "PKR 2.5 Crore" if mode == "for_sale" else "PKR 75 Thousand",
            "price_numeric": 25000000 if mode == "for_sale" else 75000,
            "beds": 4, "baths": 4, "area": "10 Marla"
        }]

    return matches


def generate_whatsapp_post(listing: dict, persona_key: str = "investor", agent: dict = None, recipient_phone: str = None) -> dict:
    """
    Generates formatted WhatsApp message text and a 100% free wa.me URL link.
    If recipient_phone is provided, targets that phone number directly.
    """
    persona = PERSONA_PROFILES.get(persona_key, PERSONA_PROFILES["investor"])
    if not agent:
        agent = random.choice(VERIFIED_AGENTS)

    title   = listing.get("title", "Featured Property")
    raw_city= listing.get("city", "Islamabad")
    city_name = raw_city.split("_")[-1] if "_" in raw_city else raw_city
    sector  = listing.get("sector") or listing.get("address") or city_name
    price   = listing.get("price", "Contact for Price")
    area    = listing.get("area", "N/A")
    beds    = listing.get("beds", "N/A")
    baths   = listing.get("baths", "N/A")
    prop_type = listing.get("property_type", "Property")
    mode    = "For Rent" if listing.get("listing_mode") == "for_rent" else "For Sale"
    desc    = (listing.get("description") or "")[:120]

    # ── Persona-specific urgency lines ───────────────────────────────────
    URGENCY = {
        "investor": [
            "⚡ Only 2 units left at launch pricing — prices rise next week.",
            "📊 Rental yield estimated at 6–8% p.a. — outperforms fixed deposits.",
            "🔒 NOC-verified | Capital-gain safe | Freehold title.",
        ],
        "luxury": [
            "✨ Exclusive VIP listing — not publicly advertised.",
            "🏆 Architecturally designed by award-winning firm.",
            "🔐 Private gated access | Concierge-ready | Investment-grade address.",
        ],
        "family": [
            "🌳 Quiet street | Top school within 5 min drive.",
            "🔐 Gated community with 24/7 security guards.",
            "🛝 Parks, mosque & market all within walking distance.",
        ],
        "first_time": [
            "💳 Easy 3-year installment plan available.",
            "📋 Clear title, NOC approved — zero legal hassle.",
            "🎁 Free home inspection + legal fee support on booking.",
        ],
    }
    urgency_lines = "\n".join(URGENCY.get(persona_key, URGENCY["investor"]))

    # ── Property specs bullets ────────────────────────────────────────────
    specs_parts = []
    if area and area != "N/A":
        specs_parts.append(f"📐 {area}")
    if beds and beds != "N/A":
        specs_parts.append(f"🛏 {beds} Bed")
    if baths and baths != "N/A":
        specs_parts.append(f"🚿 {baths} Bath")
    specs_parts.append(f"🏷 {prop_type}")
    specs_line = "  |  ".join(specs_parts)

    # ── Description line (only if available) ─────────────────────────────
    desc_block = f"\n📝 _{desc}..._\n" if desc else ""

    # ── Date stamp for urgency ────────────────────────────────────────────
    today = datetime.now().strftime("%d %b %Y")

    message = (
        f"{persona['hook']}\n"
        f"─────────────────\n\n"
        f"*🏙 {title}*\n"
        f"📍 *{sector}*   |   {mode}\n"
        f"💰 *Asking Price: {price}*\n\n"
        f"▪ {specs_line}\n"
        f"{desc_block}\n"
        f"─────────────────\n"
        f"*🎯 Why This Is The Right Move For You:*\n"
        f"{urgency_lines}\n\n"
        f"─────────────────\n"
        f"*👤 Your Dedicated Property Advisor:*\n"
        f"🧑‍💼 *{agent['name']}*  —  {agent['title']}\n"
        f"🏢 {agent['agency']}\n"
        f"📞 Call / WhatsApp: *{agent['phone']}*\n\n"
        f"*📅 Book a FREE site visit or video tour today!*\n"
        f"Simply reply *VISIT* or tap the link below:\n"
        f"🔗 {OUR_PLATFORM_URL}\n\n"
        f"📲 *Share with your friends and family, or save to yourself as a reminder.*\n\n"
        f"_Follow us for daily verified listings:_\n"
        f"💼 LinkedIn: {OUR_LINKEDIN_URL}\n"
        f"📘 Facebook: {OUR_FACEBOOK_URL}\n"
        f"📸 Instagram: {OUR_INSTAGRAM_URL}\n\n"
        f"_Listing verified as of {today}. Limited availability._"
    )

    encoded_msg = urllib.parse.quote(message)
    target_phone = recipient_phone or agent.get("phone", "")
    clean_phone = re.sub(r"[^0-9]", "", str(target_phone))
    if clean_phone.startswith("0"):
        clean_phone = "92" + clean_phone[1:]

    wa_target_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}" if clean_phone else f"https://api.whatsapp.com/send?text={encoded_msg}"
    wa_share_url  = f"https://api.whatsapp.com/send?text={encoded_msg}"

    return {
        "text":           message,
        "wa_link":        wa_target_url,
        "wa_share_link":  wa_share_url,
        "persona_title":  persona["title"],
        "agent":          agent,
        "recipient_phone": clean_phone,
    }
# ---------------------------------------------------------------------------
# Platform Invite (call this AFTER displaying the platform rating to the user)
# ---------------------------------------------------------------------------
OUR_PLATFORM_URL = "https://dhaislamabad.com.pk/"
OUR_LINKEDIN_URL = "https://www.linkedin.com/in/alishba-nasir786/"
OUR_FACEBOOK_URL = "https://facebook.com/YourPage"
OUR_INSTAGRAM_URL = "https://instagram.com/YourProfile"


def generate_platform_invite(persona_key: str = "investor", recipient_phone: str = None) -> dict:
    """
    Builds one WhatsApp-ready message combining:
      1. An urgency-framed invite to visit our own platform.
      2. A professional LinkedIn connect invite.
    """
    persona = PERSONA_PROFILES.get(persona_key, PERSONA_PROFILES["investor"])

    message = (
        f"👋 Hi! As a *{persona['title']}*, you get early access to our newest listings.\n\n"
        f"🔥 *Limited-time update:* Visit our platform now for the latest verified properties "
        f"before they're gone:\n{OUR_PLATFORM_URL}\n\n"
        f"🤝 We'd also love to stay connected professionally — follow our LinkedIn page for "
        f"market insights and new project launches:\n{OUR_LINKEDIN_URL}"
    )

    encoded_msg = urllib.parse.quote(message)
    clean_phone = re.sub(r"[^0-9]", "", str(recipient_phone or ""))
    if clean_phone.startswith("0"):
        clean_phone = "92" + clean_phone[1:]

    wa_link = (f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
               if clean_phone else f"https://api.whatsapp.com/send?text={encoded_msg}")

    return {"text": message, "wa_link": wa_link, "recipient_phone": clean_phone}


if __name__ == "__main__":
    print("Testing Persona Engine & WhatsApp Generator...")
    listings = load_inventory_csv()
    print(f"Loaded {len(listings)} listings from dataset.")

    matched = match_listings(listings, city="Islamabad", mode="for_sale")
    recipient_phone = input("\nEnter the customer's WhatsApp number (e.g. 03001234567): ").strip()
    print(f"Matched {len(matched)} properties for Islamabad For Sale.")

    if matched:
        result = generate_whatsapp_post(matched[0], persona_key="investor", recipient_phone=recipient_phone)
        invite = generate_platform_invite(persona_key="investor", recipient_phone=recipient_phone)
        print("\n--- Platform + LinkedIn invite ---")
        print(invite["text"])
        print("wa_link:", invite["wa_link"])
        print("\n" + "="*60)
        print("  GENERATED WHATSAPP MESSAGE PREVIEW")
        print("="*60)
        print(result["text"])
        print("\nFree wa.me Link:")
        print(result["wa_link"])
        print("="*60)
