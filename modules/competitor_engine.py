"""
Zameen.com Competitor Intelligence Engine
Production-grade scraper with rotating headers, proper selectors,
deep analytics and listing-level enrichment.
"""

import sys
import io

# Force UTF-8 output so emoji print correctly on Windows.
# line_buffering=True ensures every print() is flushed immediately,
# which is required for the SSE progress bar to update in real time.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
else:
    # Already UTF-8 but may still be block-buffered (e.g. when piped) — force line buffering
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

import requests
from datetime import datetime
import re
import time
import csv
import os
import random
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Request infrastructure
# ---------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
]

ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8,en-US;q=0.7",
    "en-US,en;q=0.9,ur;q=0.8",
]


def _make_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# ---------------------------------------------------------------------------
# Price helpers
# ---------------------------------------------------------------------------

def clean_price(price_text: str):
    """Convert 'PKR 2.5 Crore' -> int rupees.  Returns None on failure."""
    if not price_text:
        return None
    cleaned = re.sub(r"PKR\s*", "", str(price_text)).strip()
    match = re.search(r"([\d,]+(?:\.\d+)?)\s*(Lakh|Crore|Arab)?", cleaned, re.I)
    if not match:
        return None
    amount = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "").strip().lower()
    if unit == "lakh":
        return int(amount * 100_000)
    elif unit == "crore":
        return int(amount * 10_000_000)
    elif unit == "arab":
        return int(amount * 1_000_000_000)
    return int(amount)


def _area_to_sqft(area_text: str):
    """Normalise area to sq-ft for price-per-sqft calculations."""
    if not area_text:
        return None
    area_text = area_text.strip()
    m = re.search(r"([\d,.]+)\s*(Marla|Kanal|Sq\.?\s?Ft|Sq\.?\s?Yd)", area_text, re.I)
    if not m:
        return None
    val = float(m.group(1).replace(",", ""))
    unit = m.group(2).lower().replace(" ", "").replace(".", "")
    if "marla" in unit:
        return val * 225          # 1 Marla = 225 sq ft
    elif "kanal" in unit:
        return val * 4_500        # 1 Kanal = 20 Marla = 4500 sq ft
    elif "sqft" in unit:
        return val
    elif "sqyd" in unit:
        return val * 9
    return None


# ---------------------------------------------------------------------------
# Core scraper
# ---------------------------------------------------------------------------

def scrape_zameen(url: str, city_label: str = None, retries: int = 4):
    """
    Scrape a single Zameen listing-page URL.
    Returns a list of enriched listing dicts.
    """
    session = requests.Session()

    for attempt in range(retries):
        try:
            resp = session.get(url, headers=_make_headers(), timeout=30)
            print(f"    [{resp.status_code}] {url[:80]}")

            if resp.status_code == 403:
                print("    ⚠️  Blocked (403). Waiting longer before retry…")
                time.sleep(random.uniform(8, 15))
                continue

            if resp.status_code != 200 or len(resp.text) < 1500:
                return []

            return _parse_listings(resp.text, city_label, url)

        except requests.exceptions.Timeout:
            print(f"    ⏱ Timeout attempt {attempt+1}/{retries}")
            time.sleep(random.uniform(3, 6))
        except requests.exceptions.ConnectionError:
            print(f"    🔌 ConnectionError attempt {attempt+1}/{retries}")
            time.sleep(random.uniform(4, 8))
        except requests.exceptions.ChunkedEncodingError:
            print(f"    📦 ChunkedEncoding attempt {attempt+1}/{retries}")
            time.sleep(3)
        except Exception as e:
            print(f"    ❌ Unexpected: {e}")
            return []

    return []


def _parse_listings(html: str, city_label: str, page_url: str) -> list:
    """
    Parse listing cards from Zameen search-results HTML.
    Returns list of dicts with enriched fields.
    """
    soup = BeautifulSoup(html, "html.parser")
    listings = []

    # Zameen uses <article> or <li> with specific data attributes
    # We'll cast a wide net and filter by presence of links + price
    candidates = soup.find_all("li", {"aria-label": True})
    if not candidates:
        candidates = soup.find_all("article")
    if not candidates:
        candidates = soup.find_all("li")

    for card in candidates:
        link_tag = card.find("a", href=True)
        if not link_tag:
            continue

        full_text = card.get_text(" ", strip=True)

        # Must contain price
        price_match = re.search(r"PKR\s?([\d,.]+)\s?(Lakh|Crore|Arab)?", full_text, re.I)
        if not price_match:
            continue

        price_str = price_match.group(0)
        price_numeric = clean_price(price_str)

        # Extract beds, baths, area — pass the card element for DOM-aware extraction
        beds  = _extract_beds(card)
        baths = _extract_baths(card)
        area  = _extract_area(card)
        area_sqft = _area_to_sqft(area) if area else None
        price_per_sqft = int(price_numeric / area_sqft) if (price_numeric and area_sqft) else None

        # Property type from title or text
        title = link_tag.get("title") or link_tag.get("aria-label") or link_tag.get_text(strip=True)
        ptype = _detect_property_type(title, full_text)

        # Featured detection
        featured = _is_featured(card, full_text)

        # Photo count — badge value only, NOT raw img tag count
        photo_count = _extract_photo_count(card)

        # Description — store both the text and its length.
        # Marketing keyword analysis needs the text; quality benchmarks need the length.
        # Note: _extract_description() reads the search-result card snippet only,
        # NOT the full listing-page description (that requires visiting the detail URL).
        # Treat this as "card snippet text", not real ad copy.
        desc = _extract_description(card)
        desc_length = len(desc) if desc else 0

        # Build URL
        href = link_tag["href"]
        listing_url = href if href.startswith("http") else f"https://www.zameen.com{href}"

        listings.append({
            "title": title[:200],
            "price": price_str,
            "price_numeric": price_numeric,
            "beds": beds,
            "baths": baths,
            "area": area,
            "area_sqft": area_sqft,
            "price_per_sqft": price_per_sqft,
            "property_type": ptype,
            "featured": featured,
            "photo_count":        photo_count,
            "description":        desc,          # raw card snippet text for keyword analysis
            "description_length": desc_length,
            "city": city_label,
            "scraped_date": datetime.now().strftime("%Y-%m-%d"),
            "url": listing_url,
        })

    print(f"    ✅ Extracted {len(listings)} listings")
    return listings


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

def _extract_beds(card) -> int | None:
    """
    Extract bedroom count from a card element.
    Zameen renders beds as icon+number spans — we look at dedicated
    value elements first, then fall back to full-text regex.
    """
    # Strategy 1: look for a <span> or <li> whose text is a bare digit
    # sitting next to a bed-related sibling or aria-label
    for el in card.find_all(True):
        label = (el.get("aria-label") or el.get("title") or "").lower()
        if "bed" in label:
            t = el.get_text(strip=True)
            m = re.search(r"\d+", t)
            if m:
                return int(m.group())

    # Strategy 2: regex on full card text — handles "3 Bed", "3 Beds", "3BR"
    text = card.get_text(" ", strip=True)
    for pat in [r"(\d+)\s*Bed(?:room)?s?", r"(\d+)\s*BR\b"]:
        m = re.search(pat, text, re.I)
        if m:
            return int(m.group(1))
    return None


def _extract_baths(card) -> int | None:
    """
    Extract bathroom count from a card element using same dual strategy.
    """
    for el in card.find_all(True):
        label = (el.get("aria-label") or el.get("title") or "").lower()
        if "bath" in label or "washroom" in label:
            t = el.get_text(strip=True)
            m = re.search(r"\d+", t)
            if m:
                return int(m.group())

    text = card.get_text(" ", strip=True)
    for pat in [r"(\d+)\s*Bath(?:room)?s?", r"(\d+)\s*W(?:ash)?C\b"]:
        m = re.search(pat, text, re.I)
        if m:
            return int(m.group(1))
    return None


def _extract_area(card_or_text) -> str | None:
    """
    Extract area string from a card element or plain text.
    Also checks aria-label on dedicated area elements.
    """
    if hasattr(card_or_text, "find_all"):
        # Check aria-labeled area elements first
        for el in card_or_text.find_all(True):
            label = (el.get("aria-label") or el.get("title") or "").lower()
            if "area" in label or "size" in label:
                t = el.get_text(strip=True)
                m = re.search(r"[\d,.]+\s*(?:Marla|Kanal|Sq\.?\s?Ft|Sq\.?\s?Yd)", t, re.I)
                if m:
                    return m.group().strip()
        text = card_or_text.get_text(" ", strip=True)
    else:
        text = card_or_text

    m = re.search(r"([\d,.]+\s*(?:Marla|Kanal|Sq\.?\s?Ft|Sq\.?\s?Yd))", text, re.I)
    return m.group(1).strip() if m else None


def _extract_photo_count(card) -> int:
    """
    Extract the photo count badge Zameen renders on listing cards
    (e.g. a span showing '12' next to a camera icon).
    Falls back to 0 — we never count raw <img> tags because those
    measure thumbnail infrastructure, not listing photo galleries.
    """
    # Look for a span/div with a camera-related aria-label or class
    for el in card.find_all(True):
        label = (el.get("aria-label") or el.get("title") or "").lower()
        cls   = " ".join(el.get("class") or []).lower()
        if any(k in label or k in cls for k in ["photo", "image", "picture", "gallery", "camera"]):
            t = el.get_text(strip=True)
            m = re.search(r"\d+", t)
            if m:
                val = int(m.group())
                if 1 <= val <= 100:   # sanity-check
                    return val

    # Fallback: look for a small numeric span near an <img> inside the card
    # (Zameen sometimes renders "14" next to the thumbnail)
    imgs = card.find_all("img")
    if imgs:
        # Check next siblings of the first img for a digit
        for sib in imgs[0].next_siblings:
            if hasattr(sib, "get_text"):
                t = sib.get_text(strip=True)
                if re.fullmatch(r"\d{1,3}", t):
                    return int(t)

    # Return None — caller will omit this metric rather than report 0 incorrectly
    return None


def _detect_property_type(title: str, text: str) -> str:
    combined = (title + " " + text).lower()
    if any(k in combined for k in ["house", "villa", "bungalow", "kothi"]):
        return "House"
    if any(k in combined for k in ["flat", "apartment", "studio"]):
        return "Flat"
    if any(k in combined for k in ["plot", "land", "residential plot"]):
        return "Plot"
    if any(k in combined for k in ["commercial", "shop", "office", "warehouse", "plaza"]):
        return "Commercial"
    if "farm" in combined:
        return "Farm House"
    return "Unknown"


def _is_featured(card, text: str) -> bool:
    text_l = text.lower()
    if any(k in text_l for k in ["featured", "premium", "titanium", "super hot", "sponsored"]):
        return True
    # Some cards have a badge class or data attribute
    badge = card.find(class_=re.compile(r"(featured|premium|badge)", re.I))
    return badge is not None


def _extract_description(card) -> str:
    """Try to pull listing description text from a card."""
    # Look for a description <p> or dedicated element
    for tag in ["p", "div"]:
        for el in card.find_all(tag):
            t = el.get_text(strip=True)
            if len(t) > 40:
                return t[:500]
    return ""


# ---------------------------------------------------------------------------
# CSV persistence
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "title", "price", "price_numeric", "beds", "baths",
    "area", "area_sqft", "price_per_sqft", "property_type", "featured",
    "photo_count", "description", "description_length",
    "city", "scraped_date", "url",
]


def save_to_csv(listings: list, filename: str = "data/zameen_listings.csv"):
    if not listings:
        print("No listings to save.")
        return
    os.makedirs("data", exist_ok=True)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(listings)
    print(f"💾  Saved {len(listings)} listings → {filename}")


# ---------------------------------------------------------------------------
# HTML file scraper (local saved HTML)
# ---------------------------------------------------------------------------

def scrape_from_html_file(html_path: str, city_label: str = None) -> list:
    """
    Scrape listings from a locally saved Zameen.com HTML file.
    This is a thin wrapper around _parse_listings() — no logic is duplicated.

    Parameters
    ----------
    html_path   : str  — absolute or relative path to the .html file
    city_label  : str  — optional city name that will be tagged on each listing

    Returns
    -------
    list of enriched listing dicts (same schema as scrape_zameen())
    """
    if not os.path.exists(html_path):
        print(f"❌  File not found: {html_path}")
        return []

    print(f"📂  Reading HTML file: {html_path}")
    with open(html_path, "r", encoding="utf-8", errors="replace") as fh:
        html = fh.read()

    if len(html) < 1500:
        print("⚠️  File is too small — may not contain listing data.")
        return []

    # Derive a page_url stub so the existing pipeline stays unchanged
    page_url = f"file://{os.path.abspath(html_path)}"
    listings = _parse_listings(html, city_label, page_url)
    print(f"✅  scrape_from_html_file: extracted {len(listings)} listings from {os.path.basename(html_path)}")
    return listings



# ---------------------------------------------------------------------------
# Deep analytics
# ---------------------------------------------------------------------------

def analyze_marketing_strategy(listings: list) -> dict:
    MARKETING_KEYWORDS = {
        "luxury":     ["luxury", "premium", "designer", "modern", "brand new", "ultra"],
        "deal":       ["deal", "discount", "reduced", "final", "demand", "bargain", "best price"],
        "location":   ["prime", "hot location", "heart of", "main", "corner", "near metro", "near highway"],
        "investment": ["investment", "return", "profit", "rental income", "rental", "yield", "roi"],
        "urgency":    ["urgent", "immediate", "quick", "limited", "hurry", "final call", "last chance"],
        "new":        ["new project", "newly built", "brand new", "just launched", "new construction"],
    }
    counts      = {k: 0 for k in MARKETING_KEYWORDS}
    title_only  = {k: 0 for k in MARKETING_KEYWORDS}
    examples    = {k: [] for k in MARKETING_KEYWORDS}

    for listing in listings:
        title = listing.get("title", "").lower()
        # Use card snippet text where available; falls back to title only.
        # This is the search-result card snippet, NOT the full listing-page description.
        desc  = listing.get("description", "").lower()
        combined = title + " " + desc

        for category, words in MARKETING_KEYWORDS.items():
            if any(w in combined for w in words):
                counts[category] += 1
                if len(examples[category]) < 3:
                    examples[category].append(listing.get("title", "")[:70])
            if any(w in title for w in words):
                title_only[category] += 1

    # Top SEO keywords — from titles only (short, formulaic — good for SEO signal)
    all_words = " ".join(l.get("title", "") for l in listings).lower()
    word_freq = {}
    stop = {"for","in","a","the","of","and","is","at","to","on","with","by","are","be","or",
            "pkr","this","that","an","it","its","new","from","has","sale","rent","available"}
    for word in re.findall(r"\b[a-z]{4,}\b", all_words):
        if word not in stop:
            word_freq[word] = word_freq.get(word, 0) + 1

    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "keyword_counts":       counts,        # title + card snippet
        "keyword_title_counts": title_only,    # title only — for audit/comparison
        "keyword_examples":     examples,
        "top_seo_keywords":     top_keywords,
        # Honest scope label shown in the report methodology section
        "scan_scope": (
            "Listing title + search-card snippet text. "
            "Card snippets are short (avg ~87 chars) and are NOT full listing descriptions. "
            "Percentages reflect content visible on search results pages only."
        ),
    }


def analyze_pricing_strategy(listings: list) -> dict:
    city_data = {}
    for listing in listings:
        city = listing.get("city", "Unknown")
        price = listing.get("price_numeric")
        if not price:
            continue

        if city not in city_data:
            city_data[city] = {
                "budget": 0, "mid": 0, "premium": 0, "luxury": 0,
                "prices": [], "featured_prices": [], "ppsqft_values": [],
            }

        d = city_data[city]
        d["prices"].append(price)
        if listing.get("featured"):
            d["featured_prices"].append(price)
        if listing.get("price_per_sqft"):
            d["ppsqft_values"].append(listing["price_per_sqft"])

        if price <= 5_000_000:       d["budget"]  += 1
        elif price <= 15_000_000:    d["mid"]     += 1
        elif price <= 50_000_000:    d["premium"] += 1
        else:                        d["luxury"]  += 1

    for city, d in city_data.items():
        d["total"] = len(d["prices"])
        d["avg_price"]  = sum(d["prices"]) / d["total"] if d["total"] else 0
        d["min_price"]  = min(d["prices"]) if d["prices"] else 0
        d["max_price"]  = max(d["prices"]) if d["prices"] else 0
        # median
        s = sorted(d["prices"])
        n = len(s)
        d["median_price"] = (s[n//2] + s[n//2-1]) / 2 if n > 1 else (s[0] if s else 0)
        d["avg_featured_price"] = (
            sum(d["featured_prices"]) / len(d["featured_prices"])
            if d["featured_prices"] else d["avg_price"]
        )
        d["featured_premium"] = (
            ((d["avg_featured_price"] - d["avg_price"]) / d["avg_price"] * 100)
            if d["avg_price"] else 0
        )
        d["avg_ppsqft"] = (
            sum(d["ppsqft_values"]) / len(d["ppsqft_values"])
            if d["ppsqft_values"] else 0
        )

    return city_data


def analyze_property_types(listings: list) -> tuple:
    overall = {}
    by_city = {}
    for listing in listings:
        pt   = listing.get("property_type", "Unknown")
        city = listing.get("city", "Unknown")
        overall[pt] = overall.get(pt, 0) + 1
        by_city.setdefault(city, {})[pt] = by_city.get(city, {}).get(pt, 0) + 1

        # fix missing nested default
        by_city[city][pt] = by_city[city].get(pt, 0) + 1

    # recalculate cleanly
    by_city = {}
    for listing in listings:
        pt   = listing.get("property_type", "Unknown")
        city = listing.get("city", "Unknown")
        if city not in by_city:
            by_city[city] = {}
        by_city[city][pt] = by_city[city].get(pt, 0) + 1

    return overall, by_city


def analyze_listing_quality(listings: list) -> dict:
    """
    Measures photo badge count, description length, and field completeness.
    photo_count is None when no badge was found (not zero — we don't conflate
    'badge not found' with 'no photos').
    """
    photos, desc_lens, with_beds, with_area = [], [], 0, 0
    for l in listings:
        pc = l.get("photo_count")
        if pc is not None:           # only include listings where we found a badge
            photos.append(pc)
        if l.get("description_length"):
            desc_lens.append(l["description_length"])
        if l.get("beds"):
            with_beds += 1
        if l.get("area"):
            with_area += 1

    total = len(listings) or 1
    photo_badge_coverage = round(len(photos) / total * 100, 1)

    return {
        "avg_photos":            round(sum(photos) / len(photos), 1) if photos else None,
        "photo_badge_coverage":  photo_badge_coverage,   # % of cards where a badge was found
        "avg_desc_length":       round(sum(desc_lens) / len(desc_lens)) if desc_lens else 0,
        "beds_coverage_pct":     round(with_beds / total * 100, 1),
        "area_coverage_pct":     round(with_area / total * 100, 1),
    }


def generate_competitor_report(listings: list) -> dict:
    """Run all analytics and return one unified results dict."""
    total = len(listings)
    if total == 0:
        print("⚠️  No listings to analyze.")
        return {}

    featured_count = sum(1 for l in listings if l.get("featured"))
    marketing      = analyze_marketing_strategy(listings)
    pricing        = analyze_pricing_strategy(listings)
    prop_counts, city_prop_counts = analyze_property_types(listings)
    quality        = analyze_listing_quality(listings)

    city_avgs = {c: d["avg_price"] for c, d in pricing.items()}

    # Extraction completeness (0-100) — measures THIS SCRAPER's field coverage,
    # NOT a statement about Zameen's data quality. Renamed to avoid misleading readers.
    beds_ok  = sum(1 for l in listings if l.get("beds")) / total * 100
    area_ok  = sum(1 for l in listings if l.get("area")) / total * 100
    ppsq_ok  = sum(1 for l in listings if l.get("price_per_sqft")) / total * 100
    extraction_completeness = round((beds_ok + area_ok + ppsq_ok) / 3, 1)

    report = {
        "total_listings":        total,
        "featured_count":        featured_count,
        "marketing_analysis":    marketing,
        "pricing_analysis":      pricing,
        "city_avgs":             city_avgs,
        "property_counts":       prop_counts,
        "city_property_counts":  city_prop_counts,
        "listing_quality":       quality,
        "extraction_completeness": extraction_completeness,
        "generated_at":          datetime.now().isoformat(),
    }

    # Print quick terminal summary
    print("\n" + "="*65)
    print("  ZAMEEN.COM COMPETITOR INTELLIGENCE — QUICK SUMMARY")
    print("="*65)
    print(f"  Unique listings analysed  : {total:,}")
    print(f"  Featured listings         : {featured_count} ({featured_count/total*100:.1f}%)")
    print(f"  City×Category segments    : {len(pricing)}")
    print(f"  Extraction completeness   : {extraction_completeness}%  (scraper field coverage)")
    if city_avgs:
        exp = max(city_avgs, key=city_avgs.get)
        chp = min(city_avgs, key=city_avgs.get)
        print(f"  Most expensive segment    : {exp} — PKR {city_avgs[exp]:,.0f} avg")
        print(f"  Cheapest segment          : {chp} — PKR {city_avgs[chp]:,.0f} avg")
    print("="*65)

    return report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Verified location IDs from Zameen URL scheme:
    # zameen.com/{Category}/{City}-{loc_id}-{page}.html
    LOCATION_IDS = {
        "Islamabad":  3,
        "Lahore":     1,
        "Karachi":    2,
        "Rawalpindi": 41,
        "Faisalabad": 16,
        "Multan":     15,
        "Peshawar":   17,
        "Quetta":     18,
    }

    CATEGORIES = {
        "Houses":  "Houses_Property",
        "Flats":   "Flats_Property",
        # NOTE: "Plots_Property" URLs on Zameen appear to return the same listings
        # as Houses_Property (the category filter is applied client-side via JS,
        # not server-side). Including it produces duplicate/mislabelled data.
        # Re-enable only if you confirm the URL returns actual plot listings.
        # "Plots":   "Plots_Property",
    }

    all_listings = []
    total_combos = len(CATEGORIES) * len(LOCATION_IDS)
    combo_idx = 0

    for cat_label, cat_slug in CATEGORIES.items():
        for city, loc_id in LOCATION_IDS.items():
            combo_idx += 1
            pct = min(80.0, round((combo_idx / total_combos) * 80.0, 1))
            city_label = f"{cat_label}_{city}"
            base_url   = f"https://www.zameen.com/{cat_slug}/{city}-{loc_id}-{{}}.html"

            print(f"\n{pct:.1f}% -- Scraping Zameen.com ({city_label})...", flush=True)
            print(f"{'='*55}", flush=True)

            consecutive_empty = 0

            for page in range(1, 11):
                url = base_url.format(page)
                print(f"\n  Page {page}:", flush=True)
                listings = scrape_zameen(url, city_label)

                if not listings:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        print(f"  2 empty pages in a row -- stopping {city_label}", flush=True)
                        break
                else:
                    consecutive_empty = 0
                    all_listings.extend(listings)

                # Polite delay -- randomised to avoid rate-limiting
                time.sleep(random.uniform(2.5, 5.0))

    print(f"\n85.0% -- Processing collected listings...", flush=True)

    if not all_listings:
        print("  Live scrape returned no listings. Loading repository dataset...", flush=True)
        all_listings = load_fallback_listings()

    print(f"\n{'='*55}", flush=True)
    print(f"  TOTAL LISTINGS COLLECTED (raw): {len(all_listings):,}", flush=True)
    print(f"{'='*55}", flush=True)

    if not all_listings:
        print("No listings collected. Check network or data directory.", flush=True)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Deduplicate on URL before any analysis
    # Zameen serves the same listing across multiple category pages
    # (e.g. a house appears in both Houses_Islamabad and Plots_Islamabad).
    # Keeping duplicates inflates every count in the report.
    # ------------------------------------------------------------------
    print(f"\n90.0% -- Deduplicating listings...", flush=True)
    seen_urls = set()
    deduped = []
    for listing in all_listings:
        url_key = listing.get("url", "").split("?")[0].rstrip("/")
        if url_key and url_key not in seen_urls:
            seen_urls.add(url_key)
            deduped.append(listing)

    duplicates_removed = len(all_listings) - len(deduped)
    print(f"\n  Deduplication: removed {duplicates_removed:,} duplicates", flush=True)
    print(f"  Unique listings for analysis: {len(deduped):,}", flush=True)

    all_listings = deduped

    # Persist raw data
    save_to_csv(all_listings)

    # Deep analytics
    print(f"\n95.0% -- Generating deep competitor analytics...", flush=True)
    report_data = generate_competitor_report(all_listings)

    # Generate reports
    print(f"\n98.0% -- Rendering executive HTML reports...", flush=True)
    from report_generator import CompetitorReport
    rpt = CompetitorReport(all_listings, report_data)
    rpt.generate_all_reports()

    print(f"\n100.0% -- Competitor Intelligence Analysis Complete!", flush=True)