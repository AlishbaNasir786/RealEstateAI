# 🏢 RealEstate AI — Intelligence & Lead Generation Suite

> **Production-grade Real Estate Intelligence & Automated Lead Qualification Engine**
> Built for Pakistani property markets with dual-mode Zameen.com scraping, deep market analytics, persona profiling, and automated WhatsApp lead generation.

---

## ⚡ Quick Start

```powershell
# 1. Launch Master Unified Real Estate AI Portal (All Person A Modules + Admin/Client Switcher)
Start-Process "index.html"

# 2. Launch Standalone Persona Profiler & WhatsApp Generator
Start-Process "persona_app.html"

# 3. Run Python Persona Backend Test
python modules/persona_engine.py

# 4. Run Competitor Scraper & Intelligence Report Builder
python modules/competitor_engine.py
```

---

## 🚀 Key Modules & Architecture

### 📊 1. Dual-Mode Competitor Scraper (`modules/competitor_engine.py`)
- **Segregated Markets**: Scrapes **For Sale** (PKR lump sum) and **For Rent** (PKR/month) independently to prevent price statistical mixing.
- **Verified Zameen Endpoints**: `Rentals_Houses_Property` and `Rentals_Flats_Apartments` (zero sale-listing contamination).
- **Smart Unit Normalization**: Converts `Thousand`, `Lakh`, `Crore`, `Arab` text strings into exact PKR integer values.
- **Category Hints**: Prevents property type misclassification (`Flat` vs `House`).
- **Data Export**: Exports clean CSVs to `data/` (**4,600+ listings**).

### 📈 2. Executive Report Builder (`modules/report_generator.py`)
- **Dual Outputs**: Generates responsive HTML report (`data/competitor_report.html`) and text summary (`data/competitor_report.txt`).
- **City-by-City Intelligence**: Average/median pricing, price/sqft, featured premiums, and low-confidence flags (< 15 listings).
- **Guarded Suggestions**: Suppresses speculative strategic advice on small sample sizes.

### 🤖 3. Interactive Lead Qualification App (`persona_app.html`)
- **4-Step Wizard**: Archetype selection, target city (8 cities), sale/rent intent, budget range.
- **Strict City Isolation**: 100% strict `cityMatch && modeMatch` filter — Karachi returns **ONLY** Karachi listings (0 cross-city leakage).
- **Target Phone Modal**: Recipient number prompt with country code auto-formatting (`03001234567` ➔ `923001234567`).
- **Free WhatsApp Integration**: Uses standard `https://api.whatsapp.com/send?phone=...&text=...` deep links with automatic pop-up blocker fallback.

### ⚙️ 4. Python Persona Backend (`modules/persona_engine.py`)
- Programmatically matches CSV inventory, ranks platforms, assigns verified consultants, and builds formatted WhatsApp messages.

---

## 💡 How Platform Ratings are Calculated

The rating percentage (e.g., **96% Match**, **92% Match**) measures **Buyer Channel Conversion Likelihood**:
> *"On which channel is this specific buyer type most likely to see, respond to, and convert on a property?"*

### 🎯 Summary Matrix

| Persona Archetype | Top Channel | Match Score | Key Conversion Driver |
| :--- | :--- | :---: | :--- |
| **📈 Young Investor** | **WhatsApp Broadcast** | **96%** | Needs instant speed for pre-launch deals & high rental yields before the market buys. |
| **🔑 First-Time Homebuyer** | **Instagram Reels** | **92%** | Ages 25–34 driven by visual short video tours, modern reels & payment plan breakdowns. |
| **🏡 Family Upgrader** | **WhatsApp Groups** | **94%** | Multi-person decision: spouses share video walkthroughs in household WhatsApp groups. |
| **💎 Luxury Seeker** | **VIP WhatsApp Concierge** | **98%** | HNWIs demand 100% private, white-glove 1-on-1 concierge service (no public comments). |

---

### 🔍 Deep Dive: Evaluation Signals

> [!NOTE]
> **1. Age & Media Habits**: Young buyers (25–34) live on Instagram Reels. Family heads (35–55) use Facebook & WhatsApp groups. Corporate & expat investors engage on LinkedIn during work hours.

> [!TIP]
> **2. Speed vs. Privacy**: Investors require **0-minute alert speed** (WhatsApp Broadcast). Luxury buyers require **discreet privacy** (VIP 1-on-1 WhatsApp).

> [!IMPORTANT]
> **3. Content Format Fit**: Investors want financial data & ROI spreadsheets. Homebuyers want aesthetic video walkthroughs and clear NOC title verification.

---

## 📂 Repository Structure

```
.
├── persona_app.html           # Interactive Persona Profiler & WhatsApp Web App
├── README.md                  # Executive Documentation
├── requirements.txt           # Python Dependencies
├── data/                      # Scraped Datasets & Generated Reports
└── modules/
    ├── competitor_engine.py   # Dual-mode Zameen scraper & analytics
    ├── persona_engine.py      # Python persona profiler & WhatsApp builder
    └── report_generator.py    # Report builder & HTML layout engine
```
