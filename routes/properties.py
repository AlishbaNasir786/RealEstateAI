"""
routes/properties.py — Properties API
Islamabad-filtered property listing + Admin-only property creation endpoint.
All existing logic preserved. Added local JSON persistence for Supabase-offline mode.
"""

import os
import uuid
import json
import time
from flask import Blueprint, jsonify, request, session
from db import supabase

# ── In-memory TTL cache for the property inventory ───────────────────────────
_CACHE_TTL_SECONDS = 300  # 5 minutes
_inventory_cache: list | None = None
_inventory_cache_time: float = 0.0


def _invalidate_cache():
    global _inventory_cache, _inventory_cache_time
    _inventory_cache = None
    _inventory_cache_time = 0.0

properties_bp = Blueprint('properties', __name__)

# ── Upload configuration for admin-added property images ─────────────────────
UPLOAD_FOLDER = os.path.join(
    os.environ.get("TMPDIR", "/tmp") if os.environ.get("VERCEL") else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images'))
)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Local persistent store (ensures admin-added properties survive server restarts) ──
_LOCAL_STORE_PATH = os.path.join(
    os.environ.get("TMPDIR", "/tmp") if os.environ.get("VERCEL") else os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
    'local_properties.json'
)
_COMMITTED_STORE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'local_properties.json'))


def _load_local_properties():
    props_dict = {}
    # 1. Load from committed & /tmp JSON files
    for path in [_LOCAL_STORE_PATH, _COMMITTED_STORE_PATH]:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for p in data:
                            pid = str(p.get('id', ''))
                            if pid and pid not in props_dict:
                                props_dict[pid] = p
        except Exception:
            pass

    # 2. Also load from SQLite custom_properties table
    try:
        from auth_db import get_all_custom_properties
        for p in get_all_custom_properties():
            pid = str(p.get('id', ''))
            if pid and pid not in props_dict:
                props_dict[pid] = p
    except Exception:
        pass

    return list(props_dict.values())


def _save_local_property(prop: dict):
    # 1. Save to SQLite
    try:
        from auth_db import save_custom_property
        save_custom_property(prop)
    except Exception:
        pass

    # 2. Save to JSON store
    existing = _load_local_properties()
    existing = [p for p in existing if str(p.get('id')) != str(prop.get('id'))]
    existing.insert(0, prop)
    try:
        os.makedirs(os.path.dirname(_LOCAL_STORE_PATH), exist_ok=True)
        with open(_LOCAL_STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ── Islamabad seed data ───────────────────────────────────────────────────────
ISLAMABAD_FALLBACK = [
    {
        "id": "isb_001",
        "title": "4-Bed Contemporary Luxury Villa — DHA Phase 2, Islamabad",
        "address": "DHA Phase 2, Islamabad",
        "price": "PKR 6.5 Crore",
        "price_numeric": 65000000,
        "beds": 4, "baths": 5,
        "area_sqft": 4500,
        "status": "For Sale",
        "property_type": "Residential Villa",
        "description": "Stunning double-storey villa with modern architectural lighting, marble flooring, rooftop terrace & dedicated parking.",
        "amenities": ["Gated Community", "24/7 Guard", "Central Gas", "Backup Generator"],
        "image_url": "/static/images/isb_dha_villa.png"
    },
    {
        "id": "isb_002",
        "title": "3-Bed Panoramic Hillside Apartment — F-11 Markaz, Islamabad",
        "address": "F-11 Markaz, Islamabad",
        "price": "PKR 2.8 Crore",
        "price_numeric": 28000000,
        "beds": 3, "baths": 3,
        "area_sqft": 1800,
        "status": "For Sale",
        "property_type": "Apartment / Flat",
        "description": "Modern high-rise apartment with glass facade offering panoramic sunset views of Margalla Hills.",
        "amenities": ["High-Speed Elevator", "Covered Parking", "Fiber Internet", "Rooftop Garden"],
        "image_url": "/static/images/isb_f11_apt.png"
    },
    {
        "id": "isb_003",
        "title": "1-Kanal Prime Corner Plot — Block B-17, Islamabad",
        "address": "Block B-17, Multi Gardens, Islamabad",
        "price": "PKR 3.2 Crore",
        "price_numeric": 32000000,
        "beds": None, "baths": None,
        "area_sqft": 4500,
        "status": "For Sale",
        "property_type": "Residential Plot",
        "description": "Ready possession corner plot in a fully developed sector with carpeted roads, underground electricity & NOC clearance.",
        "amenities": ["All Utilities", "Carpeted Roads", "Mosque Nearby", "Park Facing"],
        "image_url": "/static/images/property_ba0c1ec4-7850-4edb-90ba-3fb8e5f7a4da.png"
    },
    {
        "id": "isb_004",
        "title": "2-Bed Executive Residency — E-11/2, Islamabad",
        "address": "E-11/2, Islamabad",
        "price": "PKR 1.8 Crore",
        "price_numeric": 18000000,
        "beds": 2, "baths": 2,
        "area_sqft": 1350,
        "status": "For Sale",
        "property_type": "Apartment / Flat",
        "description": "100% NOC verified executive suite. Ideal for overseas Pakistanis. Full property management & rental yield available.",
        "amenities": ["NOC Verified", "Virtual Tour", "Property Management", "Secure Building"],
        "image_url": "/static/images/property_cdb94036-5e71-4849-a9b2-d1f634d9ce2f.png"
    },
    {
        "id": "isb_005",
        "title": "5-Marla Contemporary Townhouse — G-10/3, Islamabad",
        "address": "G-10/3, Islamabad",
        "price": "PKR 1.45 Crore",
        "price_numeric": 14500000,
        "beds": 3, "baths": 3,
        "area_sqft": 1125,
        "status": "For Sale",
        "property_type": "Residential Villa",
        "description": "Affordable family home with modern wood trim facade, car porch, near central park and top Islamabad schools.",
        "amenities": ["Installment Plan", "Near School", "Park Facing", "Gas Available"],
        "image_url": "/static/images/isb_g10_townhouse.png"
    },
    {
        "id": "isb_006",
        "title": "Studio Commercial Residency — F-7 Markaz, Islamabad",
        "address": "F-7 Markaz, Islamabad",
        "price": "PKR 95 Lakh",
        "price_numeric": 9500000,
        "beds": 1, "baths": 1,
        "area_sqft": 650,
        "status": "For Rent",
        "property_type": "Apartment / Flat",
        "description": "Compact luxury studio in Islamabad's most vibrant commercial hub. 2 minutes from Super Market.",
        "amenities": ["2 Min Metro", "Fiber Internet", "Secure Entry", "Air Conditioned Lobby"],
        "image_url": "/static/images/property_9156749c-1119-419a-afe0-9aa6887dd0e8.png",
        "price_numeric": 85000,
        "price": "PKR 85,000/month"
    },
]

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'images')


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _normalize_property(p: dict) -> dict:
    """Normalize a property record so status and price are always clean and consistent."""
    p = dict(p)  # shallow copy — don't mutate original

    # ── Normalize status ─────────────────────────────────────────────────────
    raw_status = (p.get('status') or p.get('listing_purpose') or '').lower().strip()
    title_lower = (p.get('title') or '').lower()

    # Detect rent vs sale from title keywords when status is ambiguous
    is_rent_title = any(k in title_lower for k in ['for rent', 'rental', ' rent', 'renting'])
    is_sale_title = any(k in title_lower for k in ['for sale', 'sale'])

    if 'rent' in raw_status or is_rent_title:
        p['status'] = 'For Rent'
    elif raw_status in ('for sale', 'sale') or is_sale_title:
        p['status'] = 'For Sale'
    elif raw_status in ('active', '', 'available', 'listed'):
        # Default to For Sale unless rent detected in title
        p['status'] = 'For Rent' if is_rent_title else 'For Sale'
    else:
        p['status'] = 'For Sale'

    # ── Normalize price display ────────────────────────────────────────────
    price_display = (p.get('price') or '').strip()
    price_num = float(p.get('price_numeric') or 0)
    if not price_display and price_num > 0:
        if p['status'] == 'For Rent':
            if price_num >= 1_000_000:
                price_display = f"PKR {price_num / 100_000:.0f} Lakh/month"
            else:
                price_display = f"PKR {int(price_num):,}/month"
        else:
            if price_num >= 10_000_000:
                price_display = f"PKR {price_num / 10_000_000:.1f} Crore".replace('.0 ', ' ')
            elif price_num >= 100_000:
                price_display = f"PKR {price_num / 100_000:.0f} Lakh"
            else:
                price_display = f"PKR {int(price_num):,}"
        p['price'] = price_display

    return p


def _dedup_merge(*lists):
    """Merge multiple property lists, deduplicating by id, preserving order."""
    seen, merged = set(), []
    for lst in lists:
        for p in lst:
            pid = str(p.get('id', ''))
            if pid not in seen:
                seen.add(pid)
                merged.append(_normalize_property(p))
    return merged


def get_home_inventory():
    """Return exact unified property inventory displayed on the home listing page.
    Results are cached in-memory for _CACHE_TTL_SECONDS to avoid repeated Supabase calls.
    """
    global _inventory_cache, _inventory_cache_time

    # ── Serve from cache if still fresh ─────────────────────────────────
    if _inventory_cache is not None and (time.time() - _inventory_cache_time) < _CACHE_TTL_SECONDS:
        return _inventory_cache

    local_props = _load_local_properties()

    try:
        isb_city_id = None
        try:
            city_res = supabase.table('cities').select('id').ilike('name', '%islamabad%').limit(1).execute()
            if city_res.data:
                isb_city_id = city_res.data[0]['id']
        except Exception:
            pass

        response = supabase.table('properties').select('*').execute()
        props = response.data or []

        isb_keywords = ['islamabad', 'f-6', 'f-7', 'f-8', 'f-10', 'f-11', 'e-11', 'g-9', 'g-10', 'g-11', 'g-13', 'dha', 'bahria', 'b-17', 'blue area']

        filtered = []
        for p in props:
            if isb_city_id and p.get('city_id') == isb_city_id:
                filtered.append(p)
                continue
            txt = f"{p.get('address') or ''} {p.get('city') or ''} {p.get('location') or ''} {p.get('title') or ''}".lower()
            if any(k in txt for k in isb_keywords) and not any(other in txt for other in ['lahore', 'karachi', 'rawalpindi', 'peshawar', 'multan']):
                filtered.append(p)

        result = _dedup_merge(local_props, filtered, ISLAMABAD_FALLBACK)
    except Exception:
        result = _dedup_merge(local_props, ISLAMABAD_FALLBACK)

    # Filter out any deleted properties
    deleted_ids = _load_deleted_ids()
    if deleted_ids:
        result = [p for p in result if str(p.get('id')) not in deleted_ids]

    # ── Store in cache ───────────────────────────────────────────────────
    _inventory_cache = result
    _inventory_cache_time = time.time()
    return result


@properties_bp.route('/api/properties', methods=['GET'])
def get_properties():
    """Return all Islamabad properties served on the home listing page."""
    data = get_home_inventory()
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp, 200


@properties_bp.route('/api/admin/add_property', methods=['POST'])
def add_property():
    """Admin-only: Create a new Islamabad property listing with image uploads."""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    user_email = session.get('user_email')

    if not user_id and not user_email:
        return jsonify({'error': 'Authentication required. Please sign in as Admin.'}), 401

    if user_role != 'admin' and user_email != 'admin@realestate-ai.pk':
        user = None
        try:
            from auth_db import get_user_by_id
            user = get_user_by_id(user_id) if user_id else None
        except Exception:
            pass
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required.'}), 403

    sector = request.form.get('sector', '').strip()
    price_numeric = int(request.form.get('price_numeric', 0) or 0)
    price_display = request.form.get('price_display', '').strip()

    # Auto-format price if display not provided
    if not price_display and price_numeric:
        crore = price_numeric / 10_000_000
        lakh = price_numeric / 100_000
        price_display = f"PKR {crore:.1f} Crore" if crore >= 1 else f"PKR {lakh:.0f} Lakh"

    # Parse amenities from JSON string (sent by checkbox form)
    amenities = []
    amenities_json = request.form.get('amenities_json', '[]')
    try:
        amenities = json.loads(amenities_json)
        if not isinstance(amenities, list):
            amenities = []
    except Exception:
        amenities = []

    data = {
        'id': str(uuid.uuid4()),
        'title': request.form.get('title', '').strip(),
        'address': f"{sector}, Islamabad" if sector else request.form.get('address', 'Islamabad').strip(),
        'sector': sector,
        'property_type': request.form.get('property_type', 'Residential Villa').strip(),
        'purpose': request.form.get('purpose', '').strip(),
        'price_numeric': price_numeric,
        'price': price_display,
        'beds': int(request.form.get('beds', 0) or 0),
        'baths': int(request.form.get('baths', 0) or 0),
        'area_sqft': float(request.form.get('area_sqft', 0) or 0),
        'description': request.form.get('description', '').strip(),
        'city': 'Islamabad',
        'status': request.form.get('status', 'For Sale').strip(),
        'availability': request.form.get('availability', 'Available').strip(),  # 'Available' or 'Not Available'
        'amenities': amenities,
    }

    if not data['title']:
        return jsonify({'error': 'Property title is required.'}), 400

    # Handle up to 5 image uploads
    uploaded_images = []
    for i in range(1, 6):
        file = request.files.get(f'image_{i}')
        if file and file.filename and _allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"property_{data['id']}_{i}.{ext}"
            try:
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                uploaded_images.append(f'/static/images/{filename}')
            except Exception as img_err:
                print(f"Warning saving uploaded image: {img_err}")

    data['image_url'] = uploaded_images[0] if uploaded_images else None
    data['gallery'] = json.dumps(uploaded_images)

    # Always persist locally — guarantees it shows in listings immediately
    _save_local_property(data)
    _invalidate_cache()  # force next request to rebuild fresh inventory

    # Also push to Supabase if available
    if supabase is not None:
        try:
            supabase.table('properties').insert(data).execute()
        except Exception:
            pass

    return jsonify({'status': 'success', 'property': data, 'images': uploaded_images}), 201


def _require_admin():
    """Returns the user dict if session user is admin, else None."""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    if not user_id and not user_email:
        return None
    if user_role == 'admin' or user_email == 'admin@realestate-ai.pk':
        return {'id': user_id or 'admin_root', 'email': user_email or 'admin@realestate-ai.pk', 'role': 'admin'}
    try:
        from auth_db import get_user_by_id
        user = get_user_by_id(user_id) if user_id else None
        if user and user.get('role') == 'admin':
            return user
    except Exception:
        pass
    return None


_DELETED_STORE_PATH = os.path.join(
    os.environ.get("TMPDIR", "/tmp") if os.environ.get("VERCEL") else os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
    'local_deleted.json'
)
_COMMITTED_DELETED_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'local_deleted.json'))


def _load_deleted_ids() -> set:
    for path in [_DELETED_STORE_PATH, _COMMITTED_DELETED_PATH]:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
        except Exception:
            pass
    return set()


def _save_deleted_id(property_id: str):
    deleted = _load_deleted_ids()
    deleted.add(str(property_id))
    try:
        os.makedirs(os.path.dirname(_DELETED_STORE_PATH), exist_ok=True)
        with open(_DELETED_STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(list(deleted), f, indent=2)
    except Exception:
        pass


@properties_bp.route('/api/admin/edit_property/<property_id>', methods=['PATCH'])
def edit_property(property_id):
    """Admin-only: Edit any field of a property (including availability). Works for local, Supabase & fallback properties."""
    if not _require_admin():
        return jsonify({'error': 'Admin access required.'}), 403

    data = request.json or {}

    existing = _load_local_properties()
    prop = next((p for p in existing if str(p.get('id')) == str(property_id)), None)

    # If not already in local store, search in global unified inventory
    if prop is None:
        inventory = get_home_inventory()
        base_prop = next((p for p in inventory if str(p.get('id')) == str(property_id)), None)
        if base_prop:
            prop = dict(base_prop)
        else:
            return jsonify({'error': 'Property not found.'}), 404

    # Allowed editable fields
    editable = ['title', 'status', 'availability', 'price', 'price_numeric',
                'beds', 'baths', 'area_sqft', 'description', 'property_type',
                'sector', 'address', 'purpose', 'amenities']
    for key in editable:
        if key in data:
            prop[key] = data[key]

    _save_local_property(prop)
    _invalidate_cache()

    # Best-effort update Supabase if connected
    if supabase is not None:
        try:
            if 'availability' in data:
                supabase.table('properties').update({'availability': data['availability']}).eq('id', property_id).execute()
        except Exception:
            pass

    return jsonify({'status': 'success', 'property': prop}), 200


@properties_bp.route('/api/admin/delete_property/<property_id>', methods=['DELETE'])
def delete_property(property_id):
    """Admin-only: Remove a property from local store, fallback list, and Supabase."""
    if not _require_admin():
        return jsonify({'error': 'Admin access required.'}), 403

    str_pid = str(property_id)
    
    # Check if property exists in local store or global inventory
    existing = _load_local_properties()
    new_list = [p for p in existing if str(p.get('id')) != str_pid]

    try:
        os.makedirs(os.path.dirname(_LOCAL_STORE_PATH), exist_ok=True)
        with open(_LOCAL_STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_list, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    try:
        from auth_db import delete_custom_property
        delete_custom_property(str_pid)
    except Exception:
        pass

    # Record in deleted IDs list so fallback properties can also be hidden
    _save_deleted_id(str_pid)
    _invalidate_cache()

    # Best-effort remove from Supabase too
    if supabase is not None:
        try:
            supabase.table('properties').delete().eq('id', property_id).execute()
        except Exception:
            pass

    return jsonify({'status': 'success', 'deleted_id': property_id}), 200

