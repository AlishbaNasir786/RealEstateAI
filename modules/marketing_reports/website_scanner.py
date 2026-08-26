"""
website_scanner.py — Own-Site Scanner
Crawls your own website pages and extracts concrete, measurable signals
that the AI insights engine uses to identify weak points.

No third-party accounts needed — you own the site, you can scrape it freely.
"""

import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ---------------------------------------------------------------------------
# Pages to scan (extend as needed)
# ---------------------------------------------------------------------------

BASE_URL = "http://127.0.0.1:5000"

PAGES_TO_SCAN = [
    {"url": BASE_URL + "/",                    "label": "Home (Listings)"},
    {"url": BASE_URL + "/persona_app.html",    "label": "Persona & WhatsApp"},
    {"url": BASE_URL + "/competitor",          "label": "Competitor Engine"},
    {"url": BASE_URL + "/marketing_report",    "label": "Marketing Report"},
]


# ---------------------------------------------------------------------------
# Core page scanner
# ---------------------------------------------------------------------------

def scan_page(url: str, label: str = "") -> dict:
    """
    Fetches a single page and extracts SEO + content + performance signals.
    Returns a dict safe to pass to the insights engine.
    """
    result = {
        "url":           url,
        "label":         label,
        "status_code":   None,
        "load_time_ms":  None,
        "error":         None,
        # SEO
        "title":                 None,
        "title_length":          0,
        "meta_description":      None,
        "meta_desc_length":      0,
        "h1_count":              0,
        "h1_texts":              [],
        "h2_count":              0,
        "canonical":             None,
        # Content
        "word_count":            0,
        "paragraph_count":       0,
        "image_count":           0,
        "images_missing_alt":    0,
        "links_total":           0,
        "links_internal":        0,
        "links_external":        0,
        # Performance proxies
        "inline_scripts":        0,
        "inline_styles":         0,
        "external_stylesheets":  0,
        "external_scripts":      0,
        # Issues list
        "issues": [],
    }

    try:
        t0   = time.perf_counter()
        resp = requests.get(url, timeout=10)
        load_ms = round((time.perf_counter() - t0) * 1000, 1)

        result["status_code"]  = resp.status_code
        result["load_time_ms"] = load_ms

        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}"
            result["issues"].append(
                f"Page returned HTTP {resp.status_code} — not accessible"
            )
            return result

        soup = BeautifulSoup(resp.text, "html.parser")
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        # ── SEO ─────────────────────────────────────────────────────────────
        title_tag = soup.find("title")
        if title_tag:
            result["title"]        = title_tag.string or ""
            result["title_length"] = len(result["title"])
        else:
            result["issues"].append("Missing <title> tag — critical SEO gap")

        meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_desc and meta_desc.get("content"):
            result["meta_description"] = meta_desc["content"]
            result["meta_desc_length"] = len(meta_desc["content"])
        else:
            result["issues"].append("Missing meta description — hurts Google ranking")

        h1s = soup.find_all("h1")
        result["h1_count"] = len(h1s)
        result["h1_texts"] = [h.get_text(strip=True)[:80] for h in h1s]
        if len(h1s) == 0:
            result["issues"].append("No <h1> heading — poor heading structure")
        elif len(h1s) > 1:
            result["issues"].append(
                f"{len(h1s)} <h1> tags found — should be exactly 1 per page"
            )

        result["h2_count"] = len(soup.find_all("h2"))

        canonical = soup.find("link", attrs={"rel": "canonical"})
        result["canonical"] = canonical["href"] if canonical else None

        # ── Content ──────────────────────────────────────────────────────────
        body_text            = soup.get_text(" ", strip=True)
        result["word_count"] = len(body_text.split())
        result["paragraph_count"] = len(soup.find_all("p"))

        if result["word_count"] < 300:
            result["issues"].append(
                f"Thin content: only {result['word_count']} words — aim for 300+ for SEO"
            )

        # ── Images ───────────────────────────────────────────────────────────
        imgs = soup.find_all("img")
        result["image_count"]          = len(imgs)
        result["images_missing_alt"]   = sum(
            1 for img in imgs if not img.get("alt", "").strip()
        )
        if result["images_missing_alt"] > 0:
            result["issues"].append(
                f"{result['images_missing_alt']}/{len(imgs)} images missing alt text "
                f"— SEO & accessibility issue"
            )

        # ── Links ────────────────────────────────────────────────────────────
        all_links = soup.find_all("a", href=True)
        result["links_total"] = len(all_links)
        for a in all_links:
            href = a["href"]
            full = urljoin(base, href)
            if urlparse(full).netloc == urlparse(base).netloc:
                result["links_internal"] += 1
            else:
                result["links_external"] += 1

        # ── Performance proxies ──────────────────────────────────────────────
        result["inline_scripts"]       = len(soup.find_all("script", src=False))
        result["inline_styles"]        = len(soup.find_all("style"))
        result["external_stylesheets"] = len(
            soup.find_all("link", attrs={"rel": "stylesheet"})
        )
        result["external_scripts"]     = len(
            soup.find_all("script", src=True)
        )

        if load_ms > 2000:
            result["issues"].append(
                f"Slow page load: {load_ms}ms — aim for < 1000ms"
            )
        elif load_ms > 1000:
            result["issues"].append(
                f"Moderate load time: {load_ms}ms — consider optimising assets"
            )

        if result["title_length"] > 60:
            result["issues"].append(
                f"Title too long ({result['title_length']} chars) — "
                f"Google truncates at ~60 chars"
            )
        if result["meta_desc_length"] > 160:
            result["issues"].append(
                f"Meta description too long ({result['meta_desc_length']} chars) — "
                f"truncated at ~155–160 chars in search results"
            )

    except requests.exceptions.ConnectionError:
        result["error"]  = "Connection refused — server may not be running"
        result["issues"].append("Page unreachable — verify Flask server is running on port 5000")
    except requests.exceptions.Timeout:
        result["error"]  = "Request timed out after 10s"
        result["issues"].append("Page timed out — critical performance issue")
    except Exception as e:
        result["error"]  = str(e)
        result["issues"].append(f"Unexpected scan error: {e}")

    return result


# ---------------------------------------------------------------------------
# Full-site scan
# ---------------------------------------------------------------------------

def scan_listing_inventory() -> dict:
    """Fetches /api/properties from base URL to evaluate live property inventory quality."""
    url = f"{BASE_URL}/api/properties"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            props = resp.json() or []
            total = len(props)
            no_img = sum(1 for p in props if not p.get('image_url'))
            no_desc = sum(1 for p in props if not p.get('description') or len(str(p.get('description')).strip()) < 30)
            for_sale = sum(1 for p in props if (p.get('status') or '').lower() == 'for sale')
            for_rent = sum(1 for p in props if (p.get('status') or '').lower() == 'for rent')
            return {
                "total_listings": total,
                "missing_images": no_img,
                "missing_description": no_desc,
                "for_sale_count": for_sale,
                "for_rent_count": for_rent
            }
    except Exception:
        pass
    return {
        "total_listings": 0,
        "missing_images": 0,
        "missing_description": 0,
        "for_sale_count": 0,
        "for_rent_count": 0
    }


def scan_website(pages: list = None) -> dict:
    """
    Scans all configured pages and returns a combined report dict.
    `pages` is optional — defaults to PAGES_TO_SCAN.
    """
    pages = pages or PAGES_TO_SCAN
    scan_results = []

    print(f"[scanner] Scanning {len(pages)} pages...")
    for page in pages:
        print(f"  -> {page['label']} ({page['url']})")
        result = scan_page(page["url"], label=page["label"])
        scan_results.append(result)
        time.sleep(0.3)   # gentle — it's your own server

    # Scan inventory quality
    inventory = scan_listing_inventory()

    # Aggregate across all pages
    all_issues   = []
    total_images = 0
    total_missing_alt = 0
    load_times   = []
    pages_without_meta  = 0
    pages_without_title = 0

    for r in scan_results:
        all_issues.extend(
            [{"page": r["label"], "issue": iss} for iss in r.get("issues", [])]
        )
        total_images      += r.get("image_count", 0)
        total_missing_alt += r.get("images_missing_alt", 0)
        if r.get("load_time_ms") is not None:
            load_times.append(r["load_time_ms"])
        if not r.get("meta_description"):
            pages_without_meta += 1
        if not r.get("title"):
            pages_without_title += 1

    # Append inventory issues to all_issues
    if inventory["missing_images"] > 0:
        all_issues.append({
            "page": "Home (Listings)",
            "issue": f"{inventory['missing_images']} of {inventory['total_listings']} property listings are missing images"
        })
    if inventory["missing_description"] > 0:
        all_issues.append({
            "page": "Home (Listings)",
            "issue": f"{inventory['missing_description']} of {inventory['total_listings']} property listings have incomplete descriptions"
        })

    avg_load = round(sum(load_times) / len(load_times), 1) if load_times else None

    return {
        "pages":                 scan_results,
        "inventory":             inventory,
        "total_pages_scanned":   len(scan_results),
        "all_issues":            all_issues,
        "total_issues":          len(all_issues),
        "avg_load_time_ms":      avg_load,
        "total_images":          total_images,
        "images_missing_alt":    total_missing_alt,
        "pages_without_meta":    pages_without_meta,
        "pages_without_title":   pages_without_title,
        "scanned_at":            __import__('datetime').datetime.now().isoformat(),
    }

