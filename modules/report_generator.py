"""
Professional Competitor Intelligence Report Generator
Produces a stunning HTML report + plain-text summary from Zameen analytics.
Supports dual-mode output: Sale (PKR lump sum) and Rental (PKR/month) — analysed
independently so price statistics are never mixed between the two markets.
"""

import os
import re
from datetime import datetime


class CompetitorReport:
  def __init__(
    self,
    # New keyword-style API (preferred)
    sale_listings: list = None,
    sale_analysis: dict = None,
    rent_listings: list = None,
    rent_analysis: dict = None,
    # Legacy positional API (backwards-compatible)
    listings_data: list = None,
    analysis_data: dict = None,
  ):
    # Resolve legacy positional call: CompetitorReport(listings, analysis)
    if listings_data is not None and sale_listings is None:
      sale_listings = listings_data
      sale_analysis = analysis_data or {}

    self.listings  = sale_listings  or []
    self.analysis  = sale_analysis  or {}
    self.total     = len(self.listings)

    self.rent_listings = rent_listings or []
    self.rent_analysis = rent_analysis or {}
    self.rent_total    = len(self.rent_listings)

    self.timestamp = datetime.now().strftime("%B %d, %Y • %I:%M %p")
    self.ts_short  = datetime.now().strftime("%Y-%m-%d")

  # ------------------------------------------------------------------
  # Shared computed stats (single source of truth)
  # ------------------------------------------------------------------

  def _stats(self) -> dict:
    mkt  = self.analysis.get("marketing_analysis", {})
    kc  = mkt.get("keyword_counts", {})
    total = self.total or 1

    pricing = self.analysis.get("pricing_analysis", {})
    city_avgs = {c: d["avg_price"] for c, d in pricing.items() if d.get("avg_price")}

    prop_counts = self.analysis.get("property_counts", {})
    dominant_type = max(prop_counts, key=prop_counts.get) if prop_counts else "N/A"
    dominant_pct = round(prop_counts.get(dominant_type, 0) / total * 100, 1)

    premiums = [d["featured_premium"] for d in pricing.values() if d.get("featured_prices")]
    avg_premium = round(sum(premiums) / len(premiums), 1) if premiums else 0

    quality = self.analysis.get("listing_quality", {})

    return {
      "urgency_pct":   round(kc.get("urgency", 0) / total * 100, 1),
      "investment_pct":  round(kc.get("investment", 0) / total * 100, 1),
      "luxury_pct":    round(kc.get("luxury", 0) / total * 100, 1),
      "deal_pct":     round(kc.get("deal", 0) / total * 100, 1),
      "location_pct":   round(kc.get("location", 0) / total * 100, 1),
      "new_pct":     round(kc.get("new", 0) / total * 100, 1),
      "featured_pct":   round(self.analysis.get("featured_count", 0) / total * 100, 1),
      "dominant_type":  dominant_type,
      "dominant_pct":   dominant_pct,
      "avg_premium":   avg_premium,
      "city_avgs":    city_avgs,
      "most_exp_city":  max(city_avgs, key=city_avgs.get) if city_avgs else "N/A",
      "cheapest_city":  min(city_avgs, key=city_avgs.get) if city_avgs else "N/A",
      "avg_photos":    quality.get("avg_photos"),    # None if no badges found
      "avg_desc":     quality.get("avg_desc_length", 0),
      "beds_coverage":  quality.get("beds_coverage_pct", 0),
      "area_coverage":  quality.get("area_coverage_pct", 0),
      "photo_badge_cov": quality.get("photo_badge_coverage", 0),
      "extraction_completeness": self.analysis.get("extraction_completeness", 0),
      "top_keywords":   mkt.get("top_seo_keywords", []),
    }


  # ------------------------------------------------------------------
  # Growth suggestions engine
  # ------------------------------------------------------------------

  def _suggestions(self) -> list:
    s = self._stats()
    out = []

    if s["urgency_pct"] < 5:
      out.append({
        "priority": "highest", "icon": "",
        "category": "Marketing Gap",
        "title": "Urgency Messaging Barely Used",
        "stat": f"{s['urgency_pct']}% of listings",
        "description": (
          f"Only {s['urgency_pct']}% of Zameen listings use urgency "
          f"language. Buyers respond strongly to scarcity cues."
        ),
        "action": "Add 'Limited Time', 'Last Chance', countdown banners, and FOMO-driven push notifications.",
        "impact": "Higher engagement from high-intent buyers",
      })

    if s["investment_pct"] < 8:
      out.append({
        "priority": "highest", "icon": "",
        "category": "Untapped Segment",
        "title": "Investor Audience Ignored",
        "stat": f"{s['investment_pct']}% investment focus",
        "description": (
          f"Only {s['investment_pct']}% of listings target investors, "
          f"yet investors make up 30–40% of real-estate buyers in Pakistan."
        ),
        "action": "Build an 'Investor Hub' with ROI calculators, rental-yield data, and market reports.",
        "impact": "New high-value segment unlocked",
      })

    if s["avg_photos"] is not None and s["avg_photos"] < 4:
      out.append({
        "priority": "high", "icon": "",
        "category": "Listing Quality",
        "title": "Low Photo Count per Listing",
        "stat": f"Avg {s['avg_photos']} photos/listing (card badge)",
        "description": (
          f"Zameen listing cards average only {s['avg_photos']} photos per the "
          f"photo badge on search results. Listings with 10+ photos get 2× more enquiries."
        ),
        "action": "Mandate minimum 8 high-quality photos. Offer free professional photography for premium sellers.",
        "impact": "2× more clicks & enquiries",
      })

    if s["avg_desc"] < 150:
      out.append({
        "priority": "high", "icon": "",
        "category": "Content Quality",
        "title": "Short Listing Descriptions",
        "stat": f"Avg {s['avg_desc']} chars",
        "description": (
          f"Average description length is {s['avg_desc']} characters — very thin. "
          f"Rich descriptions improve SEO ranking and buyer trust."
        ),
        "action": "Provide AI-assisted description builder and require 200+ character descriptions.",
        "impact": "Better SEO + higher buyer trust",
      })

    if s["beds_coverage"] < 60:
      out.append({
        "priority": "high", "icon": "",
        "category": "Data Completeness",
        "title": "Missing Bedrooms/Bathrooms Data",
        "stat": f"Only {s['beds_coverage']}% listings have beds info",
        "description": (
          f"{100 - s['beds_coverage']}% of listings are missing bedroom count — "
          f"the #1 filter buyers use when searching."
        ),
        "action": "Make beds/baths mandatory fields. Auto-detect from description using NLP.",
        "impact": "Drastic search quality improvement",
      })

    pricing = self.analysis.get("pricing_analysis", {})
    city_avgs = s["city_avgs"]
    if city_avgs:
      overall_avg = sum(city_avgs.values()) / len(city_avgs)
      cheapest = s["cheapest_city"]
      most_exp = s["most_exp_city"]
      
      cheapest_name = cheapest.split('_')[-1] if '_' in cheapest else cheapest
      most_exp_name = most_exp.split('_')[-1] if '_' in most_exp else most_exp

      # Guard: only generate suggestion if the segment has enough data
      cheapest_data = pricing.get(cheapest, {})
      if city_avgs.get(cheapest, 0) < overall_avg * 0.80 and not cheapest_data.get("low_confidence"):
        out.append({
          "priority": "medium", "icon": "",
          "category": "Pricing Strategy",
          "title": f"Budget Opportunity in {cheapest_name}",
          "stat": f"PKR {city_avgs[cheapest]:,.0f} avg",
          "description": (
            f"{cheapest_name} is {((overall_avg - city_avgs[cheapest]) / overall_avg * 100):.0f}% "
            f"cheaper than the national average — a clear entry-point for first-time buyers."
          ),
          "action": f"Run targeted 'Affordable Homes in {cheapest_name}' campaigns for first-time buyers and middle-income families.",
          "impact": "High volume, price-sensitive segment",
        })

      # Guard: only generate suggestion if the segment has enough data
      most_exp_data = pricing.get(most_exp, {})
      if city_avgs.get(most_exp, 0) > overall_avg * 1.20 and not most_exp_data.get("low_confidence"):
        out.append({
          "priority": "medium", "icon": "",
          "category": "Pricing Strategy",
          "title": f"Luxury Premium in {most_exp_name}",
          "stat": f"PKR {city_avgs[most_exp]:,.0f} avg",
          "description": (
            f"{most_exp_name} commands a {((city_avgs[most_exp] - overall_avg) / overall_avg * 100):.0f}% "
            f"premium over the national average."
          ),
          "action": f"Develop white-glove luxury service tier for {most_exp_name} — dedicated agents, VIP tours, premium branding.",
          "impact": "Higher margin per transaction",
        })

    prop_counts = self.analysis.get("property_counts", {})
    flat_pct = round(prop_counts.get("Flat", 0) / self.total * 100, 1) if self.total else 0
    if flat_pct < 10:
      out.append({
        "priority": "medium", "icon": "",
        "category": "Product Gap",
        "title": "Flat / Apartment Inventory Thin",
        "stat": f"{flat_pct}% of listings",
        "description": (
          f"Only {flat_pct}% of Zameen listings are flats/apartments, "
          f"despite growing demand for urban apartments among young professionals."
        ),
        "action": "Recruit apartment developers as premium listing partners. Offer discounted featured slots for new apartment projects.",
        "impact": "Capture the growing urban apartment segment",
      })

    if s["location_pct"] < 10:
      out.append({
        "priority": "low", "icon": "",
        "category": "SEO Opportunity",
        "title": "Weak Neighbourhood-Level SEO",
        "stat": f"{s['location_pct']}% use location keywords",
        "description": (
          "Fewer than 1 in 10 listings use strong location keywords "
          "('near metro', 'main boulevard', 'corner plot'). "
          "These drive organic search traffic."
        ),
        "action": "Auto-tag listings with landmark proximity data and push sellers to add location details.",
        "impact": "Organic search traffic increase",
      })

    return out


  # ------------------------------------------------------------------
  # HTML helpers
  # ------------------------------------------------------------------

  @staticmethod
  def _priority_color(p: str) -> str:
    return {"highest": "#ef4444", "high": "#f97316", "medium": "#3b82f6", "low": "#8b5cf6"}.get(p, "#6366f1")

  @staticmethod
  def _priority_label(p: str) -> str:
    return {"highest": " Critical", "high": " High", "medium": "🔵 Medium", "low": "🟣 Low"}.get(p, p.title())

  @staticmethod
  def _bar(pct: float, color: str = "#6366f1", height: int = 8) -> str:
    pct = min(max(pct, 0), 100)
    return (
      f'<div style="background:rgba(255,255,255,0.1);border-radius:99px;height:{height}px;overflow:hidden;margin-top:6px">'
      f'<div style="width:{pct}%;background:{color};height:100%;border-radius:99px;'
      f'transition:width .6s ease"></div></div>'
    )

  @staticmethod
  def _badge(text: str, color: str = "#6366f1", bg: str = "#e0e7ff") -> str:
    return (
      f'<span style="display:inline-block;background:{bg};color:{color};'
      f'padding:3px 10px;border-radius:99px;font-size:11px;font-weight:700;'
      f'letter-spacing:.5px;text-transform:uppercase">{text}</span>'
    )

  @staticmethod
  def _pkr_cr(val: float) -> str:
    if val >= 1_000_000_000:
      return f"{val/1_000_000_000:.1f}B"
    if val >= 10_000_000:
      return f"{val/10_000_000:.1f} Cr"
    if val >= 100_000:
      return f"{val/100_000:.1f} L"
    return f"{val:,.0f}"


  # ------------------------------------------------------------------
  # HTML sub-sections
  # ------------------------------------------------------------------

  def _html_kpi_cards(self, s: dict) -> str:
    featured_count = self.analysis.get("featured_count", 0)
    cities = len(self.analysis.get("pricing_analysis", {}))
    pricing = self.analysis.get("pricing_analysis", {})
    all_prices = []
    for d in pricing.values():
      all_prices.extend(d.get("prices", []))
    overall_avg = sum(all_prices) / len(all_prices) if all_prices else 0

    cards = [
      ("⚡", f"{self.total:,}",       "Unique Listings",     "#6366f1", "↑ Active"),
      ("🌐", str(cities),          "City×Category Segments",  "#0ea5e9", "↑ 8 Cities"),
      ("💰", f"PKR {self._pkr_cr(overall_avg)}", "Overall Avg Price", "#10b981", "↑ Market Benchmarks"),
      ("⭐", f"{s['featured_pct']}%",    "Featured Listings",    "#f59e0b", "↑ Featured Share"),
      ("🎯", f"{s['extraction_completeness']}%", "Extraction Completeness", "#8b5cf6", "↑ Extracted Signals"),
      ("📸", str(s['avg_photos']) if s['avg_photos'] is not None else "N/A", "Avg Photos (badge)", "#ec4899", "↑ Photo Coverage"),
    ]
    html = '<div class="kpi-grid">'
    for icon, val, label, color, trend in cards:
      html += f"""
      <div class="kpi-card" style="position:relative;overflow:hidden">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <div class="kpi-icon" style="color:{color};font-size:18px">{icon}</div>
          <span style="font-size:10px;font-weight:700;color:{color};background:{color}18;padding:2px 7px;border-radius:99px">{trend}</span>
        </div>
        <div class="kpi-value" style="color:{color}">{val}</div>
        <div class="kpi-label">{label}</div>
      </div>"""
    html += "</div>"
    return html

  def _html_visual_charts_dashboard(self, s: dict) -> str:
    pricing = self.analysis.get("pricing_analysis", {})
    sorted_segs = sorted(pricing.items(), key=lambda x: x[1]["avg_price"], reverse=True)[:6]

    # Points for SVG trend curve across top markets
    points = []
    labels = []
    prices = [d["avg_price"] for _, d in sorted_segs] or [1]
    max_p = max(prices) or 1
    for idx, (seg_key, d) in enumerate(sorted_segs):
        x = 40 + idx * 85
        y = 150 - int((d["avg_price"] / max_p) * 100)
        points.append((x, y))
        parts = seg_key.split("_")
        name = parts[-1] if len(parts) >= 2 else seg_key
        labels.append((x, name, self._pkr_cr(d["avg_price"])))

    poly_pts = " ".join(f"{x},{y}" for x, y in points)
    area_pts = f"40,170 {poly_pts} {points[-1][0] if points else 465},170"

    # Property type breakdown for donut chart
    prop_counts = self.analysis.get("property_counts", {})
    total = self.total or 1
    type_colors = {"House": "#6366f1", "Flat": "#0ea5e9", "Plot": "#10b981", "Commercial": "#f59e0b", "Unknown": "#8b5cf6"}

    donut_html = ""
    legend_html = ""
    offset = 0
    circ = 2 * 3.14159 * 55  # perimeter ~ 345.5

    for ptype, count in sorted(prop_counts.items(), key=lambda x: x[1], reverse=True):
        if count == 0: continue
        pct = round(count / total * 100, 1)
        col = type_colors.get(ptype, "#38bdf8")
        dash = (pct / 100) * circ
        gap = circ - dash
        donut_html += f'<circle r="55" cx="80" cy="80" fill="transparent" stroke="{col}" stroke-width="18" stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-dashoffset="-{offset:.1f}" opacity="0.9"></circle>'
        offset += dash

        legend_html += f"""
        <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px;margin-bottom:8px">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="width:10px;height:10px;border-radius:50%;background:{col};display:inline-block"></span>
            <span style="color:#e2e8f0;font-weight:600">{ptype}</span>
          </div>
          <span style="color:#94a3b8;font-weight:700">{pct}% <small style="opacity:.6">({count:,})</small></span>
        </div>"""

    return f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;margin-top:20px">
      <!-- Line Chart Card: Price Trend -->
      <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:20px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <div>
            <div style="font-size:14px;font-weight:700;color:#f1f5f9">Price Trend Over Segments</div>
            <div style="font-size:11px;color:#64748b">Average listing price across top markets</div>
          </div>
          <span style="font-size:11px;color:#10b981;font-weight:700;background:rgba(16,185,129,0.15);padding:3px 8px;border-radius:6px">📈 Realtime Crawl</span>
        </div>
        <svg viewBox="0 0 500 200" style="width:100%;height:auto;overflow:visible">
          <defs>
            <linearGradient id="chartAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>
              <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0"/>
            </linearGradient>
          </defs>
          <!-- Grid Lines -->
          <line x1="30" y1="40" x2="470" y2="40" stroke="rgba(255,255,255,0.05)" stroke-dasharray="4"/>
          <line x1="30" y1="90" x2="470" y2="90" stroke="rgba(255,255,255,0.05)" stroke-dasharray="4"/>
          <line x1="30" y1="140" x2="470" y2="140" stroke="rgba(255,255,255,0.05)" stroke-dasharray="4"/>
          <line x1="30" y1="170" x2="470" y2="170" stroke="rgba(255,255,255,0.1)"/>
          
          <!-- Area Fill -->
          <polygon points="{area_pts}" fill="url(#chartAreaGrad)"/>
          
          <!-- Smooth Line -->
          <polyline points="{poly_pts}" fill="none" stroke="#38bdf8" stroke-width="3" stroke-linecap="round"/>
          
          <!-- Glowing Data Points & Labels -->
          {''.join(f'<circle cx="{pt[0]}" cy="{pt[1]}" r="5" fill="#38bdf8" stroke="#0f172a" stroke-width="2"/>' for pt in points)}
          {''.join(f'<text x="{lb[0]}" y="{points[i][1] - 10}" fill="#38bdf8" font-size="10" font-weight="700" text-anchor="middle">{lb[2]}</text><text x="{lb[0]}" y="188" fill="#64748b" font-size="10" font-weight="600" text-anchor="middle">{lb[1]}</text>' for i, lb in enumerate(labels))}
        </svg>
      </div>

      <!-- Donut Chart Card: Property Breakdown -->
      <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:20px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
          <div>
            <div style="font-size:14px;font-weight:700;color:#f1f5f9">Property Type Breakdown</div>
            <div style="font-size:11px;color:#64748b">Distribution by inventory category</div>
          </div>
          <span style="font-size:11px;color:#6366f1;font-weight:700;background:rgba(99,102,241,0.15);padding:3px 8px;border-radius:6px">📊 Category Share</span>
        </div>
        <div style="display:grid;grid-template-columns:160px 1fr;gap:16px;align-items:center">
          <div style="position:relative;width:160px;height:160px;margin:0 auto">
            <svg viewBox="0 0 160 160" style="transform:rotate(-90deg);width:160px;height:160px">
              {donut_html}
            </svg>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
              <span style="font-size:18px;font-weight:800;color:#fff">{self.total:,}</span>
              <span style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px">Listings</span>
            </div>
          </div>
          <div>
            {legend_html}
          </div>
        </div>
      </div>
    </div>
    """

  def _html_city_cards(self) -> str:
    pricing = self.analysis.get("pricing_analysis", {})
    prop_by_city = self.analysis.get("city_property_counts", {})
    html = '<div class="city-grid">'
    colors = ["#6366f1","#0ea5e9","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899","#14b8a6"]

    for i, (city_key, d) in enumerate(sorted(pricing.items(), key=lambda x: x[1]["avg_price"], reverse=True)):
      color = colors[i % len(colors)]
      total_city = d.get("total", 1)
      budget_pct = round(d["budget"] / total_city * 100)
      mid_pct   = round(d["mid"]   / total_city * 100)
      premium_pct = round(d["premium"] / total_city * 100)
      luxury_pct = round(d["luxury"] / total_city * 100)

      premium_dir = "▲" if d["featured_premium"] >= 0 else "▼"
      premium_col = "#ef4444" if d["featured_premium"] >= 0 else "#10b981"

      ppsqft_str = f"PKR {d['avg_ppsqft']:,.0f}/sqft" if d.get("avg_ppsqft") else "N/A"
      median_str = self._pkr_cr(d["median_price"]) if d.get("median_price") else "N/A"

      # Fix 6: show full "Category · City" label, not just the city name
      parts = city_key.split("_")
      if len(parts) >= 2:
        cat_label = parts[0]    # Houses / Flats / Plots
        city_name = "_".join(parts[1:])
      else:
        cat_label = ""
        city_name = city_key
      display_name = f"{city_name} · {cat_label}" if cat_label else city_name

      # Low-confidence warning — shown directly on the card when n < 15
      low_conf_banner = ""
      if d.get("low_confidence"):
        low_conf_banner = (
          f'<div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);border-radius:6px;'
          f'padding:6px 10px;font-size:11px;color:#fcd34d;font-weight:600;margin-bottom:10px">'
          f'Low-confidence estimate — only {total_city} listings in this segment. '
          f'Treat figures as indicative only.</div>'
        )

      # top property types in this segment
      city_props = prop_by_city.get(city_key, {})
      top_types = sorted(city_props.items(), key=lambda x: x[1], reverse=True)[:3]
      type_badges = " ".join(self._badge(f"{t} {c}", color, f"{color}22") for t, c in top_types)

      html += f"""
      <div class="city-card" style="border-top:4px solid {color}">
        <div class="city-header">
          <span class="city-name"> {display_name}</span>
          <span class="city-price" style="color:{color}">PKR {self._pkr_cr(d['avg_price'])}</span>
        </div>
        <div class="city-sub">Average Price &nbsp;|&nbsp; Median: {median_str} &nbsp;|&nbsp; {total_city} listings</div>
        {low_conf_banner}
        <div style="margin:10px 0">{type_badges}</div>
        <div class="city-meta">
          <span>📐 {ppsqft_str}</span>
          <span style="color:{premium_col}">{premium_dir} Featured {abs(d['featured_premium']):.1f}%</span>
        </div>
        <div class="dist-row">
          <div class="dist-item">
            <div class="dist-label">Budget</div>
            <div class="dist-val">{d['budget']}</div>
            {self._bar(budget_pct, "#10b981", 5)}
          </div>
          <div class="dist-item">
            <div class="dist-label">Mid</div>
            <div class="dist-val">{d['mid']}</div>
            {self._bar(mid_pct, "#0ea5e9", 5)}
          </div>
          <div class="dist-item">
            <div class="dist-label">Premium</div>
            <div class="dist-val">{d['premium']}</div>
            {self._bar(premium_pct, "#f59e0b", 5)}
          </div>
          <div class="dist-item">
            <div class="dist-label">Luxury</div>
            <div class="dist-val">{d['luxury']}</div>
            {self._bar(luxury_pct, "#ef4444", 5)}
          </div>
        </div>
      </div>"""
    html += "</div>"
    return html


  def _html_marketing_section(self, s: dict) -> str:
    mkt = self.analysis.get("marketing_analysis", {})
    kc = mkt.get("keyword_counts", {})
    total = self.total or 1

    rows = [
      ("luxury",   "Luxury / Premium",  "#f59e0b", "bg:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.2)"),
      ("location",  "Location Signals",  "#0ea5e9", "bg:rgba(14,165,233,0.1);border:1px solid rgba(14,165,233,0.2)"),
      ("deal",    "Deal / Discount",   "#10b981", "bg:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2)"),
      ("new",    "New Construction",  "#6366f1", "bg:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2)"),
      ("investment", "Investment Focus",  "#8b5cf6", "bg:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.2)"),
      ("urgency",  "Urgency / FOMO",   "#ef4444", "bg:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2)"),
    ]

    html = '<div class="mkt-grid">'
    for key, label, color, bg_raw in rows:
      count = kc.get(key, 0)
      pct  = round(count / total * 100, 1)
      bg  = bg_raw.replace("bg:", "")
      gap_badge = self._badge("GAP", "#ef4444", "rgba(239,68,68,0.15)") if pct < 5 else self._badge("Active", "#10b981", "rgba(16,185,129,0.15)")
      html += f"""
      <div class="mkt-card" style="background:{bg}">
        <div class="mkt-row">
          <span class="mkt-label" style="color:{color}">{label}</span>
          {gap_badge}
        </div>
        <div class="mkt-stat" style="color:{color}">{pct}%</div>
        <div class="mkt-count">{count:,} listings</div>
        {self._bar(pct, color, 7)}
      </div>"""
    html += "</div>"

    # Top SEO keywords
    top_kw = s.get("top_keywords", [])[:12]
    kw_html = ""
    for word, freq in top_kw:
      size = max(12, min(22, 12 + freq // 3))
      kw_html += (
        f'<span style="font-size:{size}px;color:#818cf8;background:rgba(99,102,241,0.15);'
        f'border:1px solid rgba(99,102,241,0.3);padding:4px 12px;border-radius:99px;margin:4px;display:inline-block">'
        f'{word} <small style="color:#a5b4fc">×{freq}</small></span>'
      )

    html += f"""
    <div class="keyword-cloud">
      <div class="section-sub-title">🔑 Top SEO Keywords Used by Zameen</div>
      <div style="margin-top:12px;line-height:2">{kw_html}</div>
    </div>"""
    return html

  def _html_quality_section(self, s: dict) -> str:
    # avg_photos is None when no photo badges were found on any card
    photo_val  = s["avg_photos"] if s["avg_photos"] is not None else 0
    photo_note = "" if s["avg_photos"] is not None else " (badge not found)"
    badge_cov  = s["photo_badge_cov"]

    metrics = [
      (" Avg Photos (card badge)" + photo_note, photo_val, 20, "#ec4899"),
      (" Photo Badge Coverage",         badge_cov, 100, "#f97316"),
      ("📝 Avg Description Length",        s["avg_desc"], 300, "#6366f1"),
      (" Beds Data Coverage",         s["beds_coverage"], 100, "#10b981"),
      ("📐 Area Data Coverage",          s["area_coverage"], 100, "#0ea5e9"),
    ]
    html = '<div class="quality-grid">'
    for label, val, max_val, color in metrics:
      pct = min(round((val / max_val * 100) if max_val else 0), 100)
      fmt = f"{val:.1f}" if isinstance(val, float) else str(val)
      grade_color = "#ef4444" if pct < 40 else ("#f59e0b" if pct < 70 else "#10b981")
      grade = "Poor" if pct < 40 else ("Moderate" if pct < 70 else "Good")
      html += f"""
      <div class="quality-card">
        <div class="quality-label">{label}</div>
        <div class="quality-val" style="color:{color}">{fmt}</div>
        {self._badge(grade, grade_color, grade_color + "22")}
        {self._bar(pct, color, 10)}
      </div>"""
    html += "</div>"
    return html

  def _html_suggestions(self) -> str:
    suggestions = self._suggestions()
    if not suggestions:
      return "<p>No major gaps detected — Zameen is performing well across all signals.</p>"

    html = ""
    for s in suggestions:
      color = self._priority_color(s["priority"])
      label = self._priority_label(s["priority"])
      html += f"""
      <div class="suggestion" style="border-left:5px solid {color}">
        <div class="sug-header">
          <span class="sug-icon">{s['icon']}</span>
          <div>
            <div class="sug-title">{s['title']}</div>
            <div style="display:flex;gap:8px;align-items:center;margin-top:4px">
              {self._badge(label, color, color + '1a')}
              {self._badge(s['category'], '#475569', '#f1f5f9')}
              <span class="sug-stat">{s['stat']}</span>
            </div>
          </div>
        </div>
        <div class="sug-desc">{s['description']}</div>
        <div class="sug-action">
          <strong> Action:</strong> {s['action']}
        </div>
        <div class="sug-impact"> {s['impact']}</div>
      </div>"""
    return html


  def _html_property_distribution(self) -> str:
    prop_counts = self.analysis.get("property_counts", {})
    total = self.total or 1
    colors = {"House": "#6366f1", "Flat": "#0ea5e9", "Plot": "#10b981",
         "Commercial": "#f59e0b", "Farm House": "#8b5cf6", "Unknown": "#94a3b8"}

    html = '<div class="prop-grid">'
    for ptype, count in sorted(prop_counts.items(), key=lambda x: x[1], reverse=True):
      if ptype in ('Unknown', 'Plot'):   # hide unlabelled / plot types
        continue
      pct  = round(count / total * 100, 1)
      color = colors.get(ptype, "#6366f1")
      html += f"""
      <div class="prop-card">
        <div class="prop-type" style="color:{color}">{ptype}</div>
        <div class="prop-count">{count:,}</div>
        <div class="prop-pct" style="color:{color}">{pct}%</div>
        {self._bar(pct, color, 10)}
      </div>"""
    html += "</div>"
    return html

  def _html_rental_section(self) -> str:
    """
    Render a Rental Market Intelligence section from self.rent_analysis.
    Prices are PKR/month. Returns empty string if no rental data was collected.
    """
    if not self.rent_listings:
      return (
        '<div style="color:#94a3b8;font-size:13px;padding:12px 0">'
        'No rental listings were collected in this run.'
        '</div>'
      )

    pricing = self.rent_analysis.get("pricing_analysis", {})
    if not pricing:
      return '<div style="color:#94a3b8;font-size:13px">Rental analytics unavailable.</div>'

    colors = ["#0ea5e9","#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899","#14b8a6"]
    all_rent_prices = []
    for d in pricing.values():
      all_rent_prices.extend(d.get("prices", []))
    overall_avg_rent = sum(all_rent_prices) / len(all_rent_prices) if all_rent_prices else 0

    # Summary KPI bar
    rent_featured = self.rent_analysis.get("featured_count", 0)
    rent_feat_pct = round(rent_featured / self.rent_total * 100, 1) if self.rent_total else 0

    html = f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:28px">
      <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;text-align:center">
        <div style="font-size:26px;font-weight:800;color:#0ea5e9">{self.rent_total:,}</div>
        <div style="font-size:12px;color:#64748b;margin-top:4px">Rental Listings</div>
      </div>
      <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;text-align:center">
        <div style="font-size:26px;font-weight:800;color:#0ea5e9">{len(pricing)}</div>
        <div style="font-size:12px;color:#64748b;margin-top:4px">City×Category Segments</div>
      </div>
      <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;text-align:center">
        <div style="font-size:26px;font-weight:800;color:#0ea5e9">PKR {self._pkr_cr(overall_avg_rent)}</div>
        <div style="font-size:12px;color:#64748b;margin-top:4px">Avg Monthly Rent</div>
      </div>
      <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;text-align:center">
        <div style="font-size:26px;font-weight:800;color:#0ea5e9">{rent_feat_pct}%</div>
        <div style="font-size:12px;color:#64748b;margin-top:4px">Featured Rentals</div>
      </div>
    </div>
    """

    # Per-segment rent cards
    html += '<div class="city-grid">'
    for i, (seg_key, d) in enumerate(
      sorted(pricing.items(), key=lambda x: x[1].get("avg_price", 0), reverse=True)
    ):
      color = colors[i % len(colors)]
      total_seg = d.get("total", 1) or 1

      parts = seg_key.split("_")
      # seg_key is like "Houses_Rent_Islamabad" — take last token as city, rest as label
      city_name = parts[-1]
      cat_label = "_".join(parts[:-1]).replace("_Rent", " Rent")
      display_name = f"{city_name} · {cat_label}"

      low_conf_note = (
        f' <span style="font-size:10px;color:#f59e0b;font-weight:600">⚠ Low sample ({d["total"]})</span>'
        if d.get("low_confidence") else ""
      )

      avg_r = d.get("avg_price", 0)
      med_r = d.get("median_price", 0)
      min_r = d.get("min_price", 0)
      max_r = d.get("max_price", 0)
      feat_prem = d.get("featured_premium", 0)
      prem_dir = "▲" if feat_prem >= 0 else "▼"
      prem_col = "#ef4444" if feat_prem >= 0 else "#10b981"

      html += f"""
      <div class="city-card" style="border-top:4px solid {color}">
        <div class="city-header">
          <span class="city-name">{display_name}</span>
          <span class="city-price" style="color:{color}">PKR {self._pkr_cr(avg_r)}</span>
        </div>
        <div class="city-sub">Avg/month &nbsp;|&nbsp; Median: {self._pkr_cr(med_r)} &nbsp;|&nbsp; {total_seg} listings{low_conf_note}</div>
        <table style="width:100%;font-size:12px;color:#64748b;border-collapse:collapse;margin-top:8px">
          <tr>
            <td style="padding:3px 0">Min&nbsp;rent</td>
            <td style="text-align:right;font-weight:600;color:#f1f5f9">PKR {self._pkr_cr(min_r)}</td>
          </tr>
          <tr>
            <td style="padding:3px 0">Max&nbsp;rent</td>
            <td style="text-align:right;font-weight:600;color:#f1f5f9">PKR {self._pkr_cr(max_r)}</td>
          </tr>
          <tr>
            <td style="padding:3px 0">Featured premium</td>
            <td style="text-align:right;font-weight:600;color:{prem_col}">{prem_dir} {abs(feat_prem):.1f}%</td>
          </tr>
        </table>
      </div>"""
    html += "</div>"

    html += """
    <div style="margin-top:16px;background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);border-radius:10px;
                padding:14px 18px;font-size:13px;color:#fcd34d;line-height:1.6">
      <strong>Interpretation note:</strong> Rental prices are in PKR per month as listed on Zameen.com.
      They are analysed separately from sale prices and must not be compared directly with sale figures.
      Low-confidence segments (fewer than 15 listings) are flagged.
    </div>"""

    return html


  def _html_strategic_summary(self, s: dict) -> str:
    pricing = self.analysis.get("pricing_analysis", {})
    all_prices = []
    for d in pricing.values():
      all_prices.extend(d.get("prices", []))
    overall_avg = sum(all_prices) / len(all_prices) if all_prices else 0

    most_exp = s["most_exp_city"]
    cheapest = s["cheapest_city"]
    city_avgs = s["city_avgs"]

    price_gap_pct = 0
    if city_avgs.get(most_exp) and city_avgs.get(cheapest) and city_avgs[cheapest]:
      price_gap_pct = round(
        (city_avgs[most_exp] - city_avgs[cheapest]) / city_avgs[cheapest] * 100
      )

    premium_word = "cheaper" if s["avg_premium"] < 0 else "more expensive"

    return f"""
    <div class="strategy-grid">
      <div class="strat-card" style="background:linear-gradient(135deg,rgba(99,102,241,0.12),rgba(99,102,241,0.06));border:1px solid rgba(99,102,241,0.25)">
        <div class="strat-title"> Target Investors</div>
        <div class="strat-body">
          Zameen uses investment messaging in only <strong>{s['investment_pct']}%</strong>
          of listings. Build a dedicated <em>Investor Hub</em> with ROI calculators,
          rental-yield data, and city-level market reports to capture this under-served,
          high-value audience.
        </div>
      </div>
      <div class="strat-card" style="background:linear-gradient(135deg,rgba(236,72,153,0.12),rgba(236,72,153,0.06));border:1px solid rgba(236,72,153,0.25)">
        <div class="strat-title">⏱️ Create Urgency</div>
        <div class="strat-body">
          With only <strong>{s['urgency_pct']}%</strong> of listings using urgency cues,
          you can stand out immediately. Deploy countdown timers, "X people viewing now"
          badges, and limited-time discounts to drive faster conversions.
        </div>
      </div>
      <div class="strat-card" style="background:linear-gradient(135deg,rgba(16,185,129,0.12),rgba(16,185,129,0.06));border:1px solid rgba(16,185,129,0.25)">
        <div class="strat-title"> City Positioning</div>
        <div class="strat-body">
          There is a <strong>{price_gap_pct}%</strong> price gap between
          <em>{most_exp.split("_")[-1]}</em> (premium) and
          <em>{cheapest.split("_")[-1]}</em> (affordable).
          Segment your campaigns: luxury messaging in {most_exp.split("_")[-1]},
          first-home messaging in {cheapest.split("_")[-1]}.
        </div>
      </div>
      <div class="strat-card" style="background:linear-gradient(135deg,rgba(245,158,11,0.12),rgba(245,158,11,0.06));border:1px solid rgba(245,158,11,0.25)">
        <div class="strat-title"> Win on Quality</div>
        <div class="strat-body">
          Zameen averages <strong>{s['avg_photos']} photos</strong> and
          <strong>{s['avg_desc']} chars</strong> of description per listing.
          Offer AI-assisted listings with richer media, virtual tours, and
          neighbourhood insights — quality is your most achievable differentiator.
        </div>
      </div>
    </div>"""


  # ------------------------------------------------------------------
  # Full HTML report
  # ------------------------------------------------------------------

  def generate_html_report(self, filename: str = "data/competitor_report.html") -> str:
    s  = self._stats()
    sugg = self._suggestions()
    n_critical = sum(1 for x in sugg if x["priority"] == "highest")
    n_high   = sum(1 for x in sugg if x["priority"] == "high")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zameen Competitor Intelligence Report</title>
<style>
/* ── Reset & base ───────────────────────────────── */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Plus Jakarta Sans','Segoe UI',system-ui,-apple-system,sans-serif;
   background:#090d16;color:#f1f5f9;line-height:1.6;padding:28px 20px}}
a{{color:inherit;text-decoration:none}}

/* ── Page wrapper ───────────────────────────────── */
.page{{max-width:1200px;margin:0 auto;background:#0f172a;
    border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.6);overflow:hidden;
    border:1px solid rgba(255,255,255,0.07)}}

/* ── Hero header ────────────────────────────────── */
.hero{{background:linear-gradient(135deg,#0a1628 0%,#0f1f3d 50%,#0d2240 100%);
    padding:48px 52px 40px;color:#fff;position:relative;overflow:hidden;
    border-bottom:1px solid rgba(16,185,129,0.2)}}
.hero::before{{content:'';position:absolute;inset:0;
    background:radial-gradient(ellipse at 20% 50%,rgba(16,185,129,0.12) 0%,transparent 60%),
               radial-gradient(ellipse at 80% 20%,rgba(56,189,248,0.08) 0%,transparent 50%);
    pointer-events:none}}
.hero-inner{{position:relative;z-index:1}}
.hero-eyebrow{{font-size:11px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;
    color:#10b981;margin-bottom:12px}}
.hero h1{{font-size:34px;font-weight:800;line-height:1.15;margin-bottom:8px;color:#fff}}
.hero h1 span{{color:#10b981}}
.hero-sub{{font-size:14px;color:#94a3b8;margin-top:4px}}
.hero-meta{{display:flex;gap:16px;margin-top:28px;flex-wrap:wrap}}
.hero-badge{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
   backdrop-filter:blur(8px);border-radius:12px;padding:14px 20px;text-align:center;
   transition:border-color .2s}}
.hero-badge:hover{{border-color:rgba(16,185,129,0.4)}}
.hero-badge .hb-val{{font-size:26px;font-weight:800;color:#fff}}
.hero-badge .hb-lbl{{font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:3px}}
.alert-strip{{display:flex;gap:10px;margin-top:20px;flex-wrap:wrap}}
.alert-pill{{background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.35);
   border-radius:99px;padding:5px 14px;font-size:12px;color:#fca5a5;font-weight:700}}
.alert-pill.warn{{background:rgba(245,158,11,.12);border-color:rgba(245,158,11,.3);color:#fcd34d}}

/* ── Section wrapper ────────────────────────────── */
.section{{padding:40px 52px;border-bottom:1px solid rgba(255,255,255,0.06)}}
.section:last-child{{border-bottom:none}}
.section-title{{font-size:20px;font-weight:700;color:#f1f5f9;margin-bottom:6px;
    display:flex;align-items:center;gap:10px}}
.section-desc{{font-size:13px;color:#64748b;margin-bottom:22px}}
.section-sub-title{{font-size:14px;font-weight:600;color:#94a3b8;margin-top:22px;margin-bottom:10px}}

/* ── KPI grid ───────────────────────────────────── */
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}}
.kpi-card{{background:rgba(255,255,255,0.04);border-radius:14px;padding:20px 16px;text-align:center;
    border:1px solid rgba(255,255,255,0.08);transition:transform .2s,border-color .2s}}
.kpi-card:hover{{transform:translateY(-3px);border-color:rgba(16,185,129,0.3)}}
.kpi-icon{{font-size:24px;margin-bottom:8px}}
.kpi-value{{font-size:26px;font-weight:800;color:#10b981}}
.kpi-label{{font-size:11px;color:#64748b;margin-top:4px;line-height:1.3;text-transform:uppercase;letter-spacing:.5px}}

/* ── City grid ──────────────────────────────────── */
.city-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}
.city-card{{background:rgba(255,255,255,0.04);border-radius:14px;padding:20px;
    border:1px solid rgba(255,255,255,0.08);transition:transform .2s,border-color .2s}}
.city-card:hover{{transform:translateY(-3px);border-color:rgba(16,185,129,0.25)}}
.city-header{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px}}
.city-name{{font-size:15px;font-weight:700;color:#f1f5f9}}
.city-price{{font-size:18px;font-weight:800;color:#10b981}}
.city-sub{{font-size:11px;color:#475569;margin-bottom:8px}}
.city-meta{{font-size:11px;color:#64748b;display:flex;justify-content:space-between;margin-bottom:10px}}
.dist-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}}
.dist-item{{text-align:center}}
.dist-label{{font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.5px}}
.dist-val{{font-size:14px;font-weight:700;color:#e2e8f0}}

/* ── Marketing grid ─────────────────────────────── */
.mkt-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
.mkt-card{{border-radius:12px;padding:16px;border:1px solid rgba(255,255,255,0.08);
    background:rgba(255,255,255,0.04)}}
.mkt-row{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}}
.mkt-label{{font-size:12px;font-weight:700;color:#94a3b8}}
.mkt-stat{{font-size:26px;font-weight:800;margin:4px 0 2px}}
.mkt-count{{font-size:11px;color:#475569}}
.keyword-cloud{{background:rgba(255,255,255,0.03);border-radius:12px;padding:18px;margin-top:18px;
    border:1px solid rgba(255,255,255,0.06)}}

/* ── Property distribution ──────────────────────── */
.prop-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}
.prop-card{{background:rgba(255,255,255,0.04);border-radius:12px;padding:16px;text-align:center;
    border:1px solid rgba(255,255,255,0.08)}}
.prop-type{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#94a3b8}}
.prop-count{{font-size:28px;font-weight:800;color:#f1f5f9;margin:6px 0 2px}}
.prop-pct{{font-size:13px;font-weight:600;margin-bottom:6px;color:#10b981}}

/* ── Quality cards ──────────────────────────────── */
.quality-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
.quality-card{{background:rgba(255,255,255,0.04);border-radius:12px;padding:18px;
    border:1px solid rgba(255,255,255,0.08)}}
.quality-label{{font-size:12px;color:#64748b;margin-bottom:6px}}
.quality-val{{font-size:30px;font-weight:800;color:#10b981;margin-bottom:6px}}

/* ── Suggestions ────────────────────────────────── */
.suggestion{{background:rgba(255,255,255,0.04);border-radius:14px;padding:22px;margin-bottom:14px;
   border:1px solid rgba(255,255,255,0.08)}}
.sug-header{{display:flex;gap:14px;align-items:flex-start;margin-bottom:10px}}
.sug-icon{{font-size:30px;flex-shrink:0}}
.sug-title{{font-size:16px;font-weight:700;color:#f1f5f9}}
.sug-stat{{font-size:11px;color:#64748b;font-style:italic}}
.sug-desc{{font-size:13px;color:#94a3b8;margin-bottom:12px;line-height:1.65}}
.sug-action{{background:rgba(16,185,129,0.1);border-radius:10px;padding:12px 16px;
   font-size:13px;color:#34d399;margin-bottom:10px;line-height:1.5;
   border:1px solid rgba(16,185,129,0.2)}}
.sug-impact{{font-size:12px;color:#10b981;font-weight:700}}

/* ── Strategy grid ──────────────────────────────── */
.strategy-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}}
.strat-card{{border-radius:14px;padding:22px;border:1px solid rgba(255,255,255,0.08);
    background:rgba(255,255,255,0.04)}}
.strat-title{{font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:10px}}
.strat-body{{font-size:13px;color:#94a3b8;line-height:1.7}}

/* ── Footer ─────────────────────────────────────── */
.footer{{background:rgba(255,255,255,0.03);padding:24px 52px;display:flex;
   justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;
   border-top:1px solid rgba(255,255,255,0.06)}}
.footer-brand{{color:#10b981;font-size:12px;font-weight:700}}
.footer-ts{{color:#475569;font-size:11px}}

/* ── Responsive ─────────────────────────────────── */
@media(max-width:640px){{
 .hero,.section{{padding:24px 20px}}
 .hero h1{{font-size:22px}}
 .footer{{padding:18px 20px}}
}}
</style>
</head>
<body>
<div class="page">

<!-- ═══════════════════ HERO ═══════════════════ -->
<div class="hero">
 <div class="hero-inner">
  <div class="hero-eyebrow">Zameen Competitor Intelligence</div>
  <h1> Zameen.com <span>Deep Analysis</span></h1>
  <div class="hero-sub">Pakistan Real Estate Market Intelligence Report</div>

  <div class="hero-meta">
   <div class="hero-badge">
    <div class="hb-val">{self.total:,}</div>
    <div class="hb-lbl">Listings</div>
   </div>
   <div class="hero-badge">
    <div class="hb-val">{len(self.analysis.get('pricing_analysis', {}))}</div>
    <div class="hb-lbl">Segments</div>
   </div>
   <div class="hero-badge">
    <div class="hb-val">{len(set('_'.join(k.split('_')[1:]) for k in self.analysis.get('pricing_analysis', {}).keys()))}</div>
    <div class="hb-lbl">Cities</div>
   </div>
   <div class="hero-badge">
    <div class="hb-val">{s['extraction_completeness']}%</div>
    <div class="hb-lbl">Extraction</div>
   </div>
   <div class="hero-badge">
    <div class="hb-val">{len(self._suggestions())}</div>
    <div class="hb-lbl">Opportunities</div>
   </div>
  </div>

  <div class="alert-strip">
   {'<div class="alert-pill"> ' + str(n_critical) + ' Critical Gaps Found</div>' if n_critical else ''}
   {'<div class="alert-pill warn"> ' + str(n_high) + ' High Priority Actions</div>' if n_high else ''}
    <div class="alert-pill" style="background:rgba(99,102,241,.25);border-color:rgba(99,102,241,.5);color:#c7d2fe">
     {self.timestamp}
    </div>
    <a href="../persona_app.html" target="_blank" class="alert-pill" style="background:rgba(16,185,129,.35);border-color:rgba(16,185,129,.7);color:#6ee7b7;text-decoration:none;font-weight:700;box-shadow:0 0 12px rgba(16,185,129,.3)">
     🤖 Launch Persona Profiler & WhatsApp Generator →
    </a>
   </div>
 </div>
</div>

<!-- ═══════════════════ KPIs ═══════════════════ -->
<div class="section">
 <div class="section-title"> Executive Overview</div>
 <div class="section-desc">High-level metrics from the latest Zameen.com data crawl</div>
 {self._html_kpi_cards(s)}
 {self._html_visual_charts_dashboard(s)}
</div>

<!-- ═══════════════════ CITIES ═══════════════════ -->
<div class="section">
 <div class="section-title"> City-by-City Price Intelligence</div>
 <div class="section-desc">Average, median, price/sqft and segment distribution — each card is one <strong>Category × City</strong> pair (e.g. Houses · Islamabad). Sorted by avg price high → low.</div>
 {self._html_city_cards()}
</div>

<!-- ═══════════════════ PROPERTY TYPES ═══════════════════ -->
<div class="section">
 <div class="section-title"> Property Type Distribution</div>
 <div class="section-desc">What types of properties Zameen is listing — and where the gaps are</div>
 {self._html_property_distribution()}
</div>

<!-- ═══════════════════ MARKETING ═══════════════════ -->
<div class="section">
 <div class="section-title"> Marketing Strategy Analysis</div>
 <div class="section-desc">Keyword presence in listing <strong>titles + card snippets</strong> (search-result page text only — not full listing descriptions). Percentages reflect what buyers see on search pages.</div>
 {self._html_marketing_section(s)}
</div>

<!-- ═══════════════════ LISTING QUALITY ═══════════════════ -->
<div class="section">
 <div class="section-title"> Listing Quality Benchmarks</div>
 <div class="section-desc">Photos, descriptions, and data completeness — where Zameen falls short</div>
 {self._html_quality_section(s)}
</div>

<!-- ═══════════════════ SUGGESTIONS ═══════════════════ -->
<div class="section">
 <div class="section-title"> Competitive Opportunities & Action Plan</div>
 <div class="section-desc">Ranked by business impact — these are Zameen's weak spots you can exploit</div>
 {self._html_suggestions()}
</div>





<!-- ═══════════════════ FOOTER ═══════════════════ -->
<div class="footer">
 <div class="footer-brand">Zameen Competitor Intelligence</div>
 <div class="footer-ts">Generated: {self.timestamp} &nbsp;|&nbsp; zameen.com analysis</div>
</div>

</div><!-- /page -->
</body>
</html>"""

    os.makedirs("data", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
      f.write(html)
    print(f"📄 HTML report → {filename}")
    return filename


  # ------------------------------------------------------------------
  # Plain-text report
  # ------------------------------------------------------------------

  def generate_text_report(self, filename: str = "data/competitor_report.txt") -> str:
    s    = self._stats()
    pricing = self.analysis.get("pricing_analysis", {})
    sugg  = self._suggestions()

    all_prices = []
    for d in pricing.values():
      all_prices.extend(d.get("prices", []))
    overall_avg = sum(all_prices) / len(all_prices) if all_prices else 0

    # Compute real city count for the label (e.g. 8 cities, 16 segments)
    real_cities = set()
    for seg in pricing.keys():
      parts = seg.split("_")
      real_cities.add("_".join(parts[1:]) if len(parts) >= 2 else seg)

    lines = [
      "=" * 72,
      " ZAMEEN.COM COMPETITOR INTELLIGENCE REPORT",
      f" Generated: {self.timestamp}",
      "=" * 72,
      "",
      "EXECUTIVE OVERVIEW",
      "-" * 40,
      f" Total unique listings  : {self.total:,}",
      f" Segments (category×city) : {len(pricing)} ({len(real_cities)} real cities × {len(pricing)//len(real_cities) if real_cities else '?'} categories)",
      f" Overall average price  : PKR {overall_avg:,.0f}",
      f" Featured listings    : {self.analysis.get('featured_count', 0)} ({s['featured_pct']}%)",
      f" Extraction completeness : {s['extraction_completeness']}% (scraper field coverage, not Zameen data quality)",
      f" Avg photos / listing   : {s['avg_photos'] if s['avg_photos'] is not None else 'N/A (no badge found)'}",
      f" Avg description length  : {s['avg_desc']} chars (card snippet only, not full listing page)",
      "",
      "CITY-BY-CITY PRICE INTELLIGENCE",
      "-" * 40,
    ]

    for seg_key, d in sorted(pricing.items(), key=lambda x: x[1]["avg_price"], reverse=True):
      # Fix 4: show "Category · City" not just the city name
      parts = seg_key.split("_")
      cat_label = parts[0] if len(parts) >= 2 else ""
      city_name = "_".join(parts[1:]) if len(parts) >= 2 else seg_key
      display  = f"{cat_label} · {city_name}" if cat_label else city_name

      lines += [
        f"\n {display}",
        f"  Avg Price    : PKR {d['avg_price']:,.0f} | Median: PKR {d.get('median_price', 0):,.0f}",
        f"  Min / Max    : PKR {d.get('min_price', 0):,.0f} — PKR {d.get('max_price', 0):,.0f}",
        f"  Price/sqft   : PKR {d.get('avg_ppsqft', 0):,.0f}",
        f"  Featured Premium: {d['featured_premium']:+.1f}%",
        f"  Segments    : Budget {d['budget']} | Mid {d['mid']} | Premium {d['premium']} | Luxury {d['luxury']}",
      ]

    lines += [
      "",
      "MARKETING STRATEGY ANALYSIS",
      "-" * 40,
      f" Luxury messaging   : {s['luxury_pct']}%",
      f" Location signals   : {s['location_pct']}%",
      f" Deal / Discount   : {s['deal_pct']}%",
      f" New construction   : {s['new_pct']}%",
      f" Investment focus   : {s['investment_pct']}% {'<< GAP' if s['investment_pct'] < 5 else ''}",
      f" Urgency / FOMO    : {s['urgency_pct']}%  {'<< GAP' if s['urgency_pct'] < 5 else ''}",
      "",
      " Top SEO keywords: " + ", ".join(f"{w}({c})" for w, c in s["top_keywords"][:10]),
      "",
      "COMPETITIVE OPPORTUNITIES",
      "-" * 40,
    ]

    for i, sg in enumerate(sugg, 1):
      lines += [
        f"\n {i}. [{sg['priority'].upper()}] {sg['icon']} {sg['title']}",
        f"   Stat  : {sg['stat']}",
        f"   Why  : {sg['description']}",
        f"   Action : {sg['action']}",
        f"   Impact : {sg['impact']}",
      ]

    lines += [
      "",
      "RENTAL MARKET INTELLIGENCE",
      "-" * 40,
      f"  Rental listings collected : {self.rent_total:,}",
    ]

    if self.rent_total > 0:
      rent_pricing = self.rent_analysis.get("pricing_analysis", {})
      all_rent_prices = []
      for d in rent_pricing.values():
        all_rent_prices.extend(d.get("prices", []))
      overall_avg_rent = sum(all_rent_prices) / len(all_rent_prices) if all_rent_prices else 0
      lines.append(f"  Overall avg monthly rent   : PKR {overall_avg_rent:,.0f}")
      lines.append(f"  Note: All rental prices are PKR/month and are analysed separately from sale data.")
      lines.append("")

      for seg_key, d in sorted(rent_pricing.items(), key=lambda x: x[1].get("avg_price", 0), reverse=True):
        parts = seg_key.split("_")
        city_name = parts[-1]
        cat_label = "_".join(parts[:-1]).replace("_Rent", " Rent")
        low_flag = "  [LOW CONFIDENCE < 15 listings]" if d.get("low_confidence") else ""
        lines += [
          f"\n  {cat_label} - {city_name}{low_flag}",
          f"    Avg rent   : PKR {d.get('avg_price', 0):,.0f}/month",
          f"    Median     : PKR {d.get('median_price', 0):,.0f}/month",
          f"    Range      : PKR {d.get('min_price', 0):,.0f}  -  PKR {d.get('max_price', 0):,.0f}",
          f"    Featured   : {d.get('featured_premium', 0):+.1f}%",
          f"    Listings   : {d.get('total', 0)}",
        ]
    else:
      lines.append("  No rental data collected in this run.")

    lines += [
      "",
      "=" * 72,
      "  Report generated by AI-Powered Competitor Intelligence Engine",
      "=" * 72,
    ]

    os.makedirs("data", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
      f.write("\n".join(lines))
    print(f"📄 Text report → {filename}")
    return filename

  # ------------------------------------------------------------------
  # Master entry point
  # ------------------------------------------------------------------

  def generate_all_reports(self):
    print("\n" + "=" * 60)
    print("  Generating Zameen Competitor Intelligence Reports...")
    print(f"  Sale listings   : {self.total:,}")
    print(f"  Rental listings : {self.rent_total:,}")
    print("=" * 60)
    html = self.generate_html_report()
    txt  = self.generate_text_report()
    print("\nAll reports generated successfully.")
    print(f"  HTML  -> {html}")
    print(f"  Text  -> {txt}")
    print("\n  Open the HTML file in a browser for the full visual report.")
    return {"html": html, "text": txt}