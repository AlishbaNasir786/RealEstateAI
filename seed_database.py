"""
seed_database.py — Populates all Supabase tables with realistic Pakistani real estate data.
Run: python seed_database.py
"""
import os, sys, re
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(__file__))
from db import supabase

# ─────────────────────────────────────────────
# 0. CLEAR EXISTING DATA (safe order: children first)
# ─────────────────────────────────────────────
def clear_tables():
    print("Clearing existing data...")
    for table in ['leads', 'property_images', 'properties', 'agents', 'agencies', 'areas', 'cities']:
        try:
            supabase.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"  Cleared: {table}")
        except Exception as e:
            print(f"  Could not clear {table}: {e}")

# ─────────────────────────────────────────────
# 1. CITIES
# ─────────────────────────────────────────────
CITIES = [
    {"name": "Islamabad", "slug": "islamabad", "province": "ICT",    "latitude": 33.7294, "longitude": 73.0931, "is_active": True},
    {"name": "Lahore",    "slug": "lahore",    "province": "Punjab", "latitude": 31.5204, "longitude": 74.3587, "is_active": True},
    {"name": "Karachi",   "slug": "karachi",   "province": "Sindh",  "latitude": 24.8607, "longitude": 67.0104, "is_active": True},
    {"name": "Rawalpindi","slug": "rawalpindi","province": "Punjab", "latitude": 33.5973, "longitude": 73.0479, "is_active": True},
    {"name": "Peshawar",  "slug": "peshawar",  "province": "KPK",    "latitude": 34.0150, "longitude": 71.5249, "is_active": True},
    {"name": "Multan",    "slug": "multan",    "province": "Punjab", "latitude": 30.1978, "longitude": 71.4697, "is_active": True},
]

# ─────────────────────────────────────────────
# 2. AREAS (per city)
# ─────────────────────────────────────────────
AREAS_BY_CITY = {
    "islamabad": [
        {"name": "DHA Phase 2",       "slug": "dha-phase-2-islamabad"},
        {"name": "G-13",              "slug": "g-13-islamabad"},
        {"name": "E-11",              "slug": "e-11-islamabad"},
        {"name": "F-11",              "slug": "f-11-islamabad"},
        {"name": "Bahria Town Phase 7","slug": "bahria-town-phase-7-islamabad"},
    ],
    "lahore": [
        {"name": "DHA Phase 6",       "slug": "dha-phase-6-lahore"},
        {"name": "Bahria Town Sector C","slug": "bahria-town-sector-c-lahore"},
        {"name": "Gulberg III",       "slug": "gulberg-iii-lahore"},
        {"name": "Model Town",        "slug": "model-town-lahore"},
    ],
    "karachi": [
        {"name": "DHA Phase 8",       "slug": "dha-phase-8-karachi"},
        {"name": "Clifton Block 5",   "slug": "clifton-block-5-karachi"},
        {"name": "PECHS Block 2",     "slug": "pechs-block-2-karachi"},
        {"name": "Navy Housing Scheme","slug": "navy-housing-scheme-karachi"},
    ],
    "rawalpindi": [
        {"name": "DHA Phase 1",       "slug": "dha-phase-1-rawalpindi"},
        {"name": "Bahria Town Phase 8","slug": "bahria-town-phase-8-rawalpindi"},
        {"name": "Saddar",            "slug": "saddar-rawalpindi"},
    ],
    "peshawar": [
        {"name": "Hayatabad Phase 3", "slug": "hayatabad-phase-3-peshawar"},
        {"name": "University Town",   "slug": "university-town-peshawar"},
    ],
    "multan": [
        {"name": "DHA Multan Sector A","slug": "dha-multan-sector-a"},
        {"name": "Officers Colony",   "slug": "officers-colony-multan"},
    ],
}

# ─────────────────────────────────────────────
# 3. AGENCIES
# ─────────────────────────────────────────────
AGENCIES = [
    {"name": "Premier Real Estate",      "phone": "+92300-5551234", "email": "info@premierrealestate.pk",  "website": "https://premierrealestate.pk",  "description": "Pakistan's leading residential brokerage with 20+ years of experience."},
    {"name": "Apex Luxury Properties",   "phone": "+92321-9876543", "email": "info@apexluxury.pk",         "website": "https://apexluxury.pk",         "description": "Exclusive luxury and ultra-premium property consultancy in DHA & Bahria Town."},
    {"name": "Capital Heights Realty",   "phone": "+92333-4445566", "email": "info@capitalheights.pk",     "website": "https://capitalheights.pk",     "description": "Commercial and investment portfolio specialists across major Pakistani cities."},
    {"name": "Zameen Platinum Partners", "phone": "+92345-1122334", "email": "info@zameenplatinum.pk",     "website": "https://zameenplatinum.pk",     "description": "Certified Zameen.com partner — residential, commercial, and plots nationwide."},
]

# ─────────────────────────────────────────────
# 4. AGENTS (linked to agencies)
# ─────────────────────────────────────────────
AGENTS_RAW = [
    {"name": "Tariq Mahmood",  "title": "Senior Investment Advisor",    "phone": "+923005551234", "whatsapp_number": "+923005551234", "agency_name": "Premier Real Estate",      "bio": "15 years in Islamabad & Rawalpindi premium residential markets."},
    {"name": "Zainab Chaudhry","title": "Residential Specialist",       "phone": "+923219876543", "whatsapp_number": "+923219876543", "agency_name": "Apex Luxury Properties",   "bio": "Luxury property specialist with expertise in DHA and Bahria Town across Pakistan."},
    {"name": "Bilal Farooq",   "title": "Commercial Portfolio Manager", "phone": "+923334445566", "whatsapp_number": "+923334445566", "agency_name": "Capital Heights Realty",   "bio": "Expert in commercial properties and investment portfolios in Lahore & Karachi."},
    {"name": "Hamza Alvi",     "title": "Property Consultant",          "phone": "+923451122334", "whatsapp_number": "+923451122334", "agency_name": "Zameen Platinum Partners", "bio": "Certified consultant for Zameen listings — specialises in first-time buyers."},
]

# ─────────────────────────────────────────────
# 5. PROPERTIES (raw data, IDs filled in after seeding cities/areas/agents)
# ─────────────────────────────────────────────
# listing_purpose: 'for_sale' | 'for_rent'
# property_category: 'residential' | 'commercial'
# status: 'active'
PROPERTIES_RAW = [
    # ── ISLAMABAD FOR SALE ──────────────────────────────────────────────────
    {"city": "islamabad", "area": "dha-phase-2-islamabad",          "title": "1 Kanal Luxury Executive Villa in DHA Phase 2",                 "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 65000000, "beds": 6, "baths": 7, "area_value": 1,   "area_unit": "Kanal",  "area_sqft": 4500, "featured": True,  "agent": "Zainab Chaudhry"},
    {"city": "islamabad", "area": "g-13-islamabad",                 "title": "10 Marla Brand New Modern House in G-13",                      "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 28500000, "beds": 5, "baths": 6, "area_value": 10,  "area_unit": "Marla", "area_sqft": 2250, "featured": True,  "agent": "Tariq Mahmood"},
    {"city": "islamabad", "area": "bahria-town-phase-7-islamabad",  "title": "5 Marla Stylish House in Bahria Town Phase 7",                 "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 17500000, "beds": 3, "baths": 4, "area_value": 5,   "area_unit": "Marla", "area_sqft": 1125, "featured": False, "agent": "Hamza Alvi"},
    {"city": "islamabad", "area": "e-11-islamabad",                 "title": "2400 Sq Ft Luxury Penthouse Apartment in E-11",                "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "buy", "price_numeric": 38000000, "beds": 4, "baths": 4, "area_value": 10.7,"area_unit": "Marla","area_sqft": 2400, "featured": True,  "agent": "Zainab Chaudhry"},

    # ── ISLAMABAD FOR RENT ──────────────────────────────────────────────────
    {"city": "islamabad", "area": "e-11-islamabad",                 "title": "3 Bed Luxury Apartment for Rent in E-11 Sector",              "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "rent", "price_numeric": 110000,   "beds": 3, "baths": 3, "area_value": 9.3,"area_unit": "Marla","area_sqft": 2100, "featured": True,  "agent": "Tariq Mahmood"},
    {"city": "islamabad", "area": "f-11-islamabad",                 "title": "2 Bed Executive Suite Apartment for Rent in F-11",            "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "rent", "price_numeric": 95000,    "beds": 2, "baths": 2, "area_value": 6.4,"area_unit": "Marla","area_sqft": 1450, "featured": False, "agent": "Hamza Alvi"},
    {"city": "islamabad", "area": "dha-phase-2-islamabad",          "title": "10 Marla Fully Furnished House for Rent in DHA Phase 2",      "property_category": "Residential", "property_type": "House",     "listing_purpose": "rent", "price_numeric": 175000,   "beds": 5, "baths": 5, "area_value": 10,  "area_unit": "Marla", "area_sqft": 2250, "featured": True,  "agent": "Zainab Chaudhry"},

    # ── LAHORE FOR SALE ─────────────────────────────────────────────────────
    {"city": "lahore",    "area": "dha-phase-6-lahore",             "title": "1 Kanal Corner Luxury House in DHA Phase 6 Lahore",           "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 58000000, "beds": 5, "baths": 6, "area_value": 1,   "area_unit": "Kanal",  "area_sqft": 4500, "featured": True,  "agent": "Bilal Farooq"},
    {"city": "lahore",    "area": "bahria-town-sector-c-lahore",    "title": "5 Marla Designer House in Bahria Town Sector C",              "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 18500000, "beds": 3, "baths": 4, "area_value": 5,   "area_unit": "Marla", "area_sqft": 1125, "featured": False, "agent": "Hamza Alvi"},
    {"city": "lahore",    "area": "gulberg-iii-lahore",             "title": "10 Marla Brand New House in Gulberg III Lahore",              "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 35000000, "beds": 4, "baths": 5, "area_value": 10,  "area_unit": "Marla", "area_sqft": 2250, "featured": True,  "agent": "Zainab Chaudhry"},

    # ── LAHORE FOR RENT ─────────────────────────────────────────────────────
    {"city": "lahore",    "area": "gulberg-iii-lahore",             "title": "2 Bed Park View Apartment for Rent in Gulberg III",           "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "rent", "price_numeric": 85000,    "beds": 2, "baths": 2, "area_value": 6,   "area_unit": "Marla","area_sqft": 1350, "featured": False, "agent": "Bilal Farooq"},
    {"city": "lahore",    "area": "model-town-lahore",              "title": "3 Bed Furnished Flat for Rent in Model Town Lahore",          "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "rent", "price_numeric": 120000,   "beds": 3, "baths": 3, "area_value": 8,   "area_unit": "Marla","area_sqft": 1800, "featured": True,  "agent": "Hamza Alvi"},

    # ── KARACHI FOR SALE ────────────────────────────────────────────────────
    {"city": "karachi",   "area": "dha-phase-8-karachi",            "title": "500 Sq Yd Luxury House in DHA Phase 8 Karachi",               "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 95000000, "beds": 6, "baths": 7, "area_value": 1,   "area_unit": "Kanal","area_sqft": 4500, "featured": True,  "agent": "Bilal Farooq"},
    {"city": "karachi",   "area": "clifton-block-5-karachi",        "title": "4 Bed Sea-Facing Luxury Flat in Clifton Block 5",             "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "buy", "price_numeric": 42000000, "beds": 4, "baths": 4, "area_value": 12.4,"area_unit": "Marla","area_sqft": 2800, "featured": True,  "agent": "Zainab Chaudhry"},
    {"city": "karachi",   "area": "pechs-block-2-karachi",          "title": "1500 Sq Ft Modern Apartment in PECHS Block 2",                "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "buy", "price_numeric": 18000000, "beds": 3, "baths": 3, "area_value": 6.7, "area_unit": "Marla","area_sqft": 1500, "featured": False, "agent": "Hamza Alvi"},

    # ── KARACHI FOR RENT ────────────────────────────────────────────────────
    {"city": "karachi",   "area": "navy-housing-scheme-karachi",    "title": "3 Bed Executive Penthouse for Rent in Navy Housing",          "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "rent", "price_numeric": 175000,   "beds": 3, "baths": 4, "area_value": 10.7,"area_unit": "Marla","area_sqft": 2400, "featured": True,  "agent": "Bilal Farooq"},
    {"city": "karachi",   "area": "pechs-block-2-karachi",          "title": "2 Bed Modern Apartment for Rent in PECHS Block 2",           "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "rent", "price_numeric": 75000,    "beds": 2, "baths": 2, "area_value": 5.3, "area_unit": "Marla","area_sqft": 1200, "featured": False, "agent": "Hamza Alvi"},

    # ── RAWALPINDI FOR SALE ─────────────────────────────────────────────────
    {"city": "rawalpindi","area": "dha-phase-1-rawalpindi",         "title": "10 Marla House in DHA Phase 1 Rawalpindi",                    "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 26000000, "beds": 4, "baths": 5, "area_value": 10,  "area_unit": "Marla", "area_sqft": 2250, "featured": False, "agent": "Tariq Mahmood"},
    {"city": "rawalpindi","area": "bahria-town-phase-8-rawalpindi", "title": "5 Marla House in Bahria Town Phase 8 Rawalpindi",             "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 14500000, "beds": 3, "baths": 3, "area_value": 5,   "area_unit": "Marla", "area_sqft": 1125, "featured": False, "agent": "Hamza Alvi"},

    # ── RAWALPINDI FOR RENT ─────────────────────────────────────────────────
    {"city": "rawalpindi","area": "saddar-rawalpindi",              "title": "3 Bed Apartment for Rent in Saddar Rawalpindi",               "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "rent", "price_numeric": 65000,    "beds": 3, "baths": 3, "area_value": 7.1, "area_unit": "Marla","area_sqft": 1600, "featured": False, "agent": "Tariq Mahmood"},

    # ── PESHAWAR ────────────────────────────────────────────────────────────
    {"city": "peshawar",  "area": "hayatabad-phase-3-peshawar",     "title": "1 Kanal Luxury House in Hayatabad Phase 3 Peshawar",          "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 45000000, "beds": 5, "baths": 6, "area_value": 1,   "area_unit": "Kanal",  "area_sqft": 4500, "featured": True,  "agent": "Bilal Farooq"},
    {"city": "peshawar",  "area": "university-town-peshawar",       "title": "3 Bed Flat for Rent in University Town Peshawar",            "property_category": "Residential", "property_type": "Apartment", "listing_purpose": "rent", "price_numeric": 58000,    "beds": 3, "baths": 3, "area_value": 7.6, "area_unit": "Marla","area_sqft": 1700, "featured": False, "agent": "Hamza Alvi"},

    # ── MULTAN ──────────────────────────────────────────────────────────────
    {"city": "multan",    "area": "dha-multan-sector-a",            "title": "10 Marla House in DHA Multan Sector A",                      "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 21000000, "beds": 4, "baths": 5, "area_value": 10,  "area_unit": "Marla", "area_sqft": 2250, "featured": False, "agent": "Tariq Mahmood"},
    {"city": "multan",    "area": "officers-colony-multan",         "title": "5 Marla House for Sale in Officers Colony Multan",           "property_category": "Residential", "property_type": "House",     "listing_purpose": "buy", "price_numeric": 12500000, "beds": 3, "baths": 3, "area_value": 5,   "area_unit": "Marla", "area_sqft": 1125, "featured": False, "agent": "Hamza Alvi"},
]

# High quality Unsplash images (free, no auth needed)
IMAGE_SETS = {
    "House":     ["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800", "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"],
    "Apartment": ["https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800", "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800"],
}

def slug_from_title(title):
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

# ─────────────────────────────────────────────
# MAIN SEED
# ─────────────────────────────────────────────
def seed():
    clear_tables()
    
    # --- CITIES ---
    print("\nSeeding cities...")
    city_ids = {}
    for c in CITIES:
        r = supabase.table('cities').insert(c).execute()
        cid = r.data[0]['id']
        city_ids[c['slug']] = cid
        print(f"  + {c['name']} -> {cid}")

    # --- AREAS ---
    print("\nSeeding areas...")
    area_ids = {}
    for city_slug, areas in AREAS_BY_CITY.items():
        cid = city_ids.get(city_slug)
        if not cid:
            continue
        for a in areas:
            r = supabase.table('areas').insert({"city_id": cid, "name": a["name"], "slug": a["slug"]}).execute()
            area_ids[a['slug']] = r.data[0]['id']
            print(f"  + {a['name']} ({city_slug})")

    # --- AGENCIES ---
    print("\nSeeding agencies...")
    agency_ids = {}
    for ag in AGENCIES:
        r = supabase.table('agencies').insert(ag).execute()
        agency_ids[ag['name']] = r.data[0]['id']
        print(f"  + {ag['name']}")

    # --- AGENTS ---
    print("\nSeeding agents...")
    agent_ids = {}
    for ag in AGENTS_RAW:
        agency_id = agency_ids.get(ag.pop('agency_name', None))
        payload = {**ag, "agency_id": agency_id, "is_active": True}
        r = supabase.table('agents').insert(payload).execute()
        agent_ids[ag['name']] = r.data[0]['id']
        print(f"  + {ag['name']}")

    # --- PROPERTIES ---
    print("\nSeeding properties...")
    property_ids = []
    for p in PROPERTIES_RAW:
        city_slug  = p.pop('city')
        area_slug  = p.pop('area')
        agent_name = p.pop('agent')

        city_id  = city_ids.get(city_slug)
        area_id  = area_ids.get(area_slug)
        agent_id = agent_ids.get(agent_name)

        prop_type = p.get('property_type', 'House')
        # Map property type to valid property_category constraint
        category_map = {'House': 'Houses', 'Apartment': 'Flats'}
        valid_category = category_map.get(prop_type, 'Commercial')
        
        payload = {
            **p,
            "property_category": valid_category,
            "slug":              slug_from_title(p['title']),
            "city_id":           city_id,
            "area_id":           area_id,
            "agent_id":          agent_id,
            "currency":          "PKR",
            "status":            "active",
            "description":       f"A premium {p.get('property_type','property').lower()} located in one of Pakistan's most sought-after areas. Verified title, immediate availability.",
            "views_count":       0,
        }

        r = supabase.table('properties').insert(payload).execute()
        pid = r.data[0]['id']
        property_ids.append({"id": pid, "type": prop_type})
        print(f"  + {p['title'][:55]}...")

    # --- PROPERTY IMAGES ---
    print("\nSeeding property images...")
    for item in property_ids:
        imgs = IMAGE_SETS.get(item['type'], IMAGE_SETS['House'])
        for i, img_url in enumerate(imgs):
            supabase.table('property_images').insert({
                "property_id": item['id'],
                "url":         img_url,
                "thumbnail_url": img_url.replace('w=800', 'w=400'),
                "alt_text":    "Property photograph",
                "is_primary":  (i == 0),
                "sort_order":  i,
            }).execute()
        print(f"  + {len(imgs)} images for property {item['id'][:8]}...")

    print("\n✅ Seeding complete!")
    print(f"  Cities:    {len(city_ids)}")
    print(f"  Areas:     {len(area_ids)}")
    print(f"  Agencies:  {len(agency_ids)}")
    print(f"  Agents:    {len(agent_ids)}")
    print(f"  Properties:{len(property_ids)}")

if __name__ == "__main__":
    seed()
