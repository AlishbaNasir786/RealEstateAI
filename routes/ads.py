"""
routes/ads.py — Blueprint for Hyper-Personalized Advertisement Engine
Provides REST API endpoints for fetching segments, retrieving properties,
generating personalized ad campaigns, and saving ad variants.
"""

from flask import Blueprint, jsonify, request
import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import supabase
from modules.ad_personalization import get_all_segments, get_segment, generate_ad_campaign

ads_bp = Blueprint('ads_bp', __name__)

_saved_campaigns = []


@ads_bp.route('/api/ads/segments', methods=['GET'])
def list_segments():
    """Return all buyer personas / segments with metadata."""
    return jsonify({
        "status": "success",
        "segments": get_all_segments()
    })


@ads_bp.route('/api/ads/properties', methods=['GET'])
def list_properties():
    """
    Return properties for dropdown selection.
    Fetches from Supabase DB, or returns structured default list if DB is empty.
    """
    try:
        res = supabase.table('properties').select('id, title, location, price, bedrooms, bathrooms, area_sqft').limit(20).execute()
        props = res.data or []
    except Exception as e:
        print(f"[routes/ads] Supabase fetch error: {e}")
        props = []

    if not props:
        props = [
            {
                "id": "prop_1",
                "title": "Luxury 1-Kanal Villa in DHA Phase 6",
                "location": "DHA Phase 6, Lahore",
                "price": "PKR 4.5 Crore",
                "bedrooms": 5,
                "bathrooms": 6,
                "area_sqft": 4500,
                "features": ["Gated Security", "Near Top Schools", "Lush Lawn", "Designer Interior"]
            },
            {
                "id": "prop_2",
                "title": "Modern 2-Bed Luxury Apartment in E-11",
                "location": "E-11/2, Islamabad",
                "price": "PKR 1.8 Crore",
                "bedrooms": 2,
                "bathrooms": 2,
                "area_sqft": 1350,
                "features": ["High Rental Yield", "Near Metro", "Smart Lift", "Fiber Internet"]
            },
            {
                "id": "prop_3",
                "title": "Prime Commercial Office Space in Gulberg III",
                "location": "Gulberg III, Lahore",
                "price": "PKR 3.2 Crore",
                "bedrooms": 0,
                "bathrooms": 2,
                "area_sqft": 2000,
                "features": ["High Footfall", "11% Projected Yield", "Dedicated Parking", "Corporate Hub"]
            },
            {
                "id": "prop_4",
                "title": "Bespoke Sky Penthouse in DHA Phase 8",
                "location": "DHA Phase 8, Karachi",
                "price": "PKR 8.5 Crore",
                "bedrooms": 4,
                "bathrooms": 5,
                "area_sqft": 5200,
                "features": ["Panoramic Ocean View", "Private Jacuzzi", "Smart Automation", "VIP Valet"]
            },
            {
                "id": "prop_5",
                "title": "Affordable 3-Bed House on 3-Year Installments",
                "location": "Bahria Town Sector C, Lahore",
                "price": "PKR 1.45 Crore",
                "bedrooms": 3,
                "bathrooms": 3,
                "area_sqft": 1125,
                "features": ["15% Down Payment", "3-Year Installment Plan", "Possession on 50%", "No Hidden Fee"]
            }
        ]

    return jsonify({
        "status": "success",
        "properties": props
    })


@ads_bp.route('/api/ads/generate', methods=['POST'])
def generate_ads():
    """
    Generates multi-platform ad variants for a given segment and property.
    Body JSON:
    {
      "segment": "family",
      "property": { ... property object or custom inputs ... },
      "force_refresh": false
    }
    """
    data = request.get_json() or {}
    segment_key = data.get("segment", "family")
    property_info = data.get("property") or {}
    force_refresh = data.get("force_refresh", False)

    if not property_info:
        return jsonify({"error": "Property details required"}), 400

    campaign = generate_ad_campaign(segment_key, property_info, force_refresh=force_refresh)
    return jsonify({
        "status": "success",
        "campaign": campaign
    })


@ads_bp.route('/api/ads/save', methods=['POST'])
def save_campaign():
    """Save an ad campaign variant to favorites list."""
    data = request.get_json() or {}
    data["saved_at"] = datetime.now().isoformat()
    _saved_campaigns.append(data)
    return jsonify({
        "status": "success",
        "message": "Campaign saved successfully",
        "total_saved": len(_saved_campaigns)
    })


@ads_bp.route('/api/ads/saved', methods=['GET'])
def get_saved_campaigns():
    """Return all saved ad campaigns."""
    return jsonify({
        "status": "success",
        "saved_campaigns": _saved_campaigns
    })
