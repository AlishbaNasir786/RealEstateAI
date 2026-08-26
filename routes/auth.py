"""
routes/auth.py — Authentication & Dynamic Banner Routes
Handles user registration, login, Google OAuth, persona segment saving,
and dynamic banner ad retrieval matching the user's persona.
"""

from flask import Blueprint, jsonify, request, session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auth_db import (
    create_user, authenticate_user, authenticate_google_user,
    get_user_by_id, update_user_segment, update_user_phone
)
from modules.ad_personalization.segments import get_segment, SEGMENTS
from modules.ad_personalization.ad_generator import generate_ad_campaign
from db import supabase

auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    """Register a new user account with email & password."""
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    full_name = data.get("full_name", "").strip()
    segment = data.get("segment")
    phone = data.get("phone", "").strip()

    if not email or not password or not full_name:
        return jsonify({"error": "Name, email, and password are required."}), 400

    res = create_user(email=email, password=password, full_name=full_name,
                      segment=segment, phone=phone or None)
    if "error" in res:
        return jsonify(res), 400

    session["user_id"]    = res["id"]
    session["user_email"] = res.get("email", "")
    session["user_name"]  = res.get("full_name", "")
    session["user_phone"] = res.get("phone", "") or ""
    return jsonify({"status": "success", "user": res})


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user with email & password."""
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    phone = data.get("phone", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    res = authenticate_user(email=email, password=password)
    if "error" in res:
        return jsonify(res), 401

    # If user provided a phone during login, update it in DB
    if phone:
        res = update_user_phone(res["id"], phone)

    session["user_id"]    = res["id"]
    session["user_email"] = res.get("email", "")
    session["user_name"]  = res.get("full_name", "")
    session["user_phone"] = res.get("phone", "") or ""
    return jsonify({"status": "success", "user": res})


@auth_bp.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Handle Continue with Google OAuth authentication."""

    data = request.get_json() or {}
    email = data.get("email", "user@gmail.com").strip()
    full_name = data.get("full_name", "Google User").strip()
    google_id = data.get("google_id", "google_123456789").strip()

    res = authenticate_google_user(email=email, full_name=full_name, google_id=google_id)
    session["user_id"]    = res["id"]
    session["user_email"] = res.get("email", "")
    session["user_name"]  = res.get("full_name", "")
    return jsonify({"status": "success", "user": res})


@auth_bp.route('/api/auth/me', methods=['GET'])
def get_me():
    """Return currently authenticated user state."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False, "user": None})

    user = get_user_by_id(user_id)
    if not user:
        session.pop("user_id", None)
        return jsonify({"authenticated": False, "user": None})

    return jsonify({"authenticated": True, "user": user})


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Clear session."""
    session.pop("user_id", None)
    return jsonify({"status": "success", "message": "Logged out successfully"})


@auth_bp.route('/api/auth/segment', methods=['POST'])
def save_segment():
    """Save user persona segment preference."""
    data = request.get_json() or {}
    segment = data.get("segment", "").strip().lower()

    if segment not in SEGMENTS:
        return jsonify({"error": f"Invalid segment. Choose from: {list(SEGMENTS.keys())}"}), 400

    user_id = session.get("user_id")
    if user_id:
        user = update_user_segment(user_id, segment)
    else:
        # For guest session
        session["guest_segment"] = segment
        user = {"id": "guest", "segment": segment, "full_name": "Guest Visitor"}

    return jsonify({"status": "success", "user": user, "segment": segment})


@auth_bp.route('/api/auth/banner', methods=['GET'])
def get_personalized_banner():
    """
    Returns matching database property listing & hyper-personalized banner ad
    tailored to the user's active segment.
    """
    user_id = session.get("user_id")
    user = get_user_by_id(user_id) if user_id else None

    active_segment = user.get("segment") if user and user.get("segment") else session.get("guest_segment", "family")

    # Fetch matching property from database or seed list matching the persona
    listing = _get_matching_listing_for_segment(active_segment)
    campaign = generate_ad_campaign(active_segment, listing)

    return jsonify({
        "status": "success",
        "segment": get_segment(active_segment),
        "listing": listing,
        "banner_ad": campaign["platforms"]["meta"]
    })


def _get_matching_listing_for_segment(segment: str) -> dict:
    """Fetch matching real estate listing from DB based on persona priorities."""
    try:
        res = supabase.table('properties').select('*').limit(10).execute()
        props = res.data or []
    except Exception:
        props = []

    if not props:
        props = [
            {
                "id": "prop_fam_1",
                "title": "Luxury 1-Kanal Villa near Top Schools",
                "location": "DHA Phase 6, Lahore",
                "price": "PKR 4.5 Crore",
                "beds": "5 Beds",
                "area": "1 Kanal",
                "features": ["Gated Security", "Near Top Schools", "Lush Community Parks", "Safe Neighborhood"]
            },
            {
                "id": "prop_inv_1",
                "title": "Commercial Office in Gulberg III (11% Rental Yield)",
                "location": "Gulberg III, Lahore",
                "price": "PKR 3.2 Crore",
                "beds": "Commercial",
                "area": "2000 Sq. Ft.",
                "features": ["High Rental Yield", "High Footfall Belt", "Strong Capital Growth", "Tenanted"]
            },
            {
                "id": "prop_ovs_1",
                "title": "2-Bed Luxury Residence (100% NOC Verified)",
                "location": "E-11/2, Islamabad",
                "price": "PKR 1.8 Crore",
                "beds": "2 Beds",
                "area": "1350 Sq. Ft.",
                "features": ["100% Legal NOC Clearance", "HD Virtual Walkthrough", "Property Management Included", "Overseas Preferred"]
            },
            {
                "id": "prop_lux_1",
                "title": "Architectural Masterpiece Penthouse",
                "location": "DHA Phase 8, Karachi",
                "price": "PKR 8.5 Crore",
                "beds": "4 Beds",
                "area": "5200 Sq. Ft.",
                "features": ["Panoramic Ocean View", "Smart Home Automation", "Private Jacuzzi", "VIP Valet"]
            },
            {
                "id": "prop_bud_1",
                "title": "Affordable 3-Bed Home on 3-Year Installments",
                "location": "Bahria Town Sector C, Lahore",
                "price": "PKR 1.45 Crore",
                "beds": "3 Beds",
                "area": "1125 Sq. Ft.",
                "features": ["15% Down Payment", "3-Year Installment Plan", "Possession on 50%", "No Hidden Fees"]
            },
            {
                "id": "prop_ten_1",
                "title": "Modern Fiber-Ready Studio Apartment",
                "location": "F-11 Markaz, Islamabad",
                "price": "PKR 95 Lakh",
                "beds": "1 Bed",
                "area": "650 Sq. Ft.",
                "features": ["2 Mins from Metro", "High-Speed Fiber Ready", "Vibrant Food Street", "Low Maintenance"]
            }
        ]

    # Match segment to specific property style
    seg = segment.lower()
    if seg == "investor":
        return props[1] if len(props) > 1 else props[0]
    elif seg == "overseas":
        return props[2] if len(props) > 2 else props[0]
    elif seg == "luxury":
        return props[3] if len(props) > 3 else props[0]
    elif seg == "budget":
        return props[4] if len(props) > 4 else props[0]
    elif seg == "tenant":
        return props[5] if len(props) > 5 else props[0]
    else:
        return props[0]


# ── /api/sector-videos — returns all sector promo videos from DB ──────────────
@auth_bp.route('/api/sector-videos', methods=['GET'])
def get_sector_videos():
    """
    Returns all sector promotional videos stored in the sector_videos table.
    Each record contains: id, sector, title, tagline, description, video_url.
    Fully dynamic — driven entirely by the database.
    """
    import sqlite3
    from auth_db import DB_FILE
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, sector, title, tagline, description, video_url FROM sector_videos ORDER BY sector"
        ).fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'videos': [dict(r) for r in rows]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'videos': [], 'error': str(e)}), 500
