import os
import re
import json
import threading
# Use built-in urllib so Vercel bundle-size stripping can never break this
try:
    import requests as http_requests
except ImportError:
    import urllib.request as _urllib_req
    import urllib.error as _urllib_err
    import ssl as _ssl
    import json as _json_mod

    class _FakeResp:
        def __init__(self, status, data):
            self.status_code = status
            self.text = data.decode('utf-8', errors='replace')
            self.content = data
        def json(self):
            return _json_mod.loads(self.text)

    class _HttpShim:
        def _request(self, method, url, json=None, headers=None, timeout=20, params=None):
            if params:
                from urllib.parse import urlencode
                url = url + '?' + urlencode(params)
            body = _json_mod.dumps(json).encode() if json else None
            hdrs = {'Content-Type': 'application/json', **(headers or {})}
            req = _urllib_req.Request(url, data=body, headers=hdrs, method=method)
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = _ssl.CERT_NONE
            try:
                with _urllib_req.urlopen(req, timeout=timeout, context=ctx) as r:
                    return _FakeResp(r.status, r.read())
            except _urllib_err.HTTPError as e:
                return _FakeResp(e.code, e.read())
            except Exception as e:
                raise RuntimeError(str(e))

        def post(self, url, json=None, headers=None, timeout=20, **kw):
            return self._request('POST', url, json=json, headers=headers, timeout=timeout)

        def get(self, url, headers=None, timeout=20, params=None, **kw):
            return self._request('GET', url, headers=headers, timeout=timeout, params=params)

    http_requests = _HttpShim()
from flask import Blueprint, request, jsonify, session
from modules.persona_engine import generate_whatsapp_post
from routes.properties import get_home_inventory

persona_bp = Blueprint('persona', __name__)

# ── Green API — Free WhatsApp API ────────────────────────────────────────
# Sign up FREE at https://green-api.com → create Developer instance → scan QR
# → copy idInstance and apiTokenInstance into .env:
#   GREEN_API_INSTANCE_ID=1234567890
#   GREEN_API_TOKEN=your_token_here
GREEN_API_INSTANCE_ID = os.environ.get('GREEN_API_INSTANCE_ID', '') or '710722700714'
GREEN_API_TOKEN       = os.environ.get('GREEN_API_TOKEN', '') or '89d888065d5145268673445bd17a69ac8822854268d8447ab2'
GREEN_API_BASE        = os.environ.get('GREEN_API_URL', 'https://7107.api.greenapi.com') or 'https://7107.api.greenapi.com'


def _clean_phone(raw: str) -> str:
    """Normalise phone to digits only in international format (e.g. 923001234567)."""
    digits = re.sub(r'[^0-9]', '', str(raw or ''))
    if digits.startswith('0'):
        digits = '92' + digits[1:]
    return digits


def _send_via_greenapi(phone: str, text: str) -> dict:
    """
    Send WhatsApp message via Green API (free developer plan).
    Endpoint: POST /waInstance{id}/sendMessage/{token}
    chatId format: 923001234567@c.us
    """
    clean = _clean_phone(phone)
    if not clean or len(clean) < 7:
        return {'success': False, 'error': 'Invalid phone number'}

    if not GREEN_API_INSTANCE_ID or not GREEN_API_TOKEN:
        return {
            'success': False,
            'setup_required': True,
            'error': (
                'Green API credentials not set. '
                'Sign up free at https://green-api.com, create a Developer instance, '
                'scan QR with your WhatsApp, then add GREEN_API_INSTANCE_ID and '
                'GREEN_API_TOKEN to .env and restart the server.'
            )
        }

    url = f'{GREEN_API_BASE}/waInstance{GREEN_API_INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN}'
    try:
        resp = http_requests.post(
            url,
            json={
                'chatId': f'{clean}@c.us',
                'message': text,
            },
            timeout=20
        )
        resp_json = resp.json() if resp.content else {}
        # Green API returns {"idMessage": "..."}  on success
        if resp.status_code == 200 and resp_json.get('idMessage'):
            return {'success': True, 'idMessage': resp_json['idMessage']}
        else:
            err = resp_json.get('message') or resp_json.get('error') or resp.text[:200]
            return {'success': False, 'error': err}
    except Exception as exc:
        return {'success': False, 'error': str(exc)}

IMAGES_MAP_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'property_images.json')


def _get_image_map():
    try:
        if os.path.exists(IMAGES_MAP_PATH):
            with open(IMAGES_MAP_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


# ── Budget bands for PURCHASE (PKR total) ────────────────────────────────
BUDGET_RANGES_SALE = {
    'mid':     (5_000_000,   25_000_000),
    'premium': (25_000_001,  60_000_000),
    'luxury':  (60_000_001, 9_999_999_999),
}

# ── Budget bands for RENT (PKR per month) ────────────────────────────────
BUDGET_RANGES_RENT = {
    'mid':     (30_000,    120_000),
    'premium': (120_001,   300_000),
    'luxury':  (300_001, 9_999_999),
}


# ── /api/sectors — returns all unique sectors from the live database ──────────
@persona_bp.route('/api/sectors', methods=['GET'])
def get_sectors():
    """
    Returns all unique sectors extracted from the property database.
    Both persona wizard and listing search bar use this to stay in sync
    with the actual inventory — nothing hardcoded.
    """
    try:
        all_props = get_home_inventory()
        purpose   = request.args.get('purpose', '')   # optional: 'sale' or 'rent'

        import re as _re

        # Known canonical casings
        CANONICAL = {
            'dha':          'DHA',
            'bahria town':  'Bahria Town',
            'b-17':         'B-17',
            'pwd':          'PWD',
            'cbr':          'CBR',
            'multi gardens':'Multi Gardens',
            'gulberg':      'Gulberg',
            'blue area':    'Blue Area',
            'naval anchorage': 'Naval Anchorage',
        }

        def normalise_sector(label):
            """Strip sub-sector suffix (E-11/2 → E-11) and fix casing."""
            label = label.strip()
            # Strip trailing /digit sub-sector (F-7/2 → F-7, G-10/3 → G-10)
            label = _re.sub(r'(/\d+)+$', '', label).strip()
            # Check canonical overrides
            low = label.lower()
            if low in CANONICAL:
                return CANONICAL[low]
            # Standard sector pattern: upper-case the letter part (f-7 → F-7)
            m = _re.match(r'^([a-zA-Z]+)-(\d+)$', label)
            if m:
                return m.group(1).upper() + '-' + m.group(2)
            return label

        def extract_sector_key(prop):
            sec = (prop.get('sector') or '').strip()
            if sec:
                return normalise_sector(sec)
            addr = (prop.get('address') or '').strip()
            m = _re.search(
                r'\b([A-Za-z]-\d+(?:/\d+)?|DHA|Bahria\s*Town|PWD|CBR|B-17|Multi\s*Gardens|Gulberg|Naval\s*Anchorage|Blue\s*Area)\b',
                addr, _re.IGNORECASE
            )
            if m:
                return normalise_sector(m.group(1).strip())
            # Use first part of address as label
            return addr.split(',')[0].strip() if addr else ''

        seen   = {}   # key (lower) -> display label
        for p in all_props:
            # optional purpose filter
            if purpose:
                status = (p.get('status') or '').lower()
                title  = (p.get('title')  or '').lower()
                is_rent_prop = 'rent' in status or 'for rent' in title
                if purpose in ('rent', 'for_rent') and not is_rent_prop:
                    continue
                if purpose in ('sale', 'for_sale') and is_rent_prop:
                    continue

            label = extract_sector_key(p)
            if label:
                seen[label.lower()] = label   # deduplicate by lowercase key

        sectors = sorted(seen.values(), key=lambda s: s.lower())
        return jsonify({'success': True, 'sectors': sectors}), 200

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'sectors': [], 'error': str(exc)}), 500


@persona_bp.route('/api/persona/match', methods=['POST'])
def match_persona():
    try:
        data         = request.json or {}
        persona_type = data.get('persona_type', 'investor')
        sector_name  = (data.get('city') or 'Islamabad').strip().lower()
        purpose      = data.get('purpose', 'sale')   # 'sale' or 'rent'
        budget_key   = data.get('budget', 'mid')

        is_rent = purpose in ('rent', 'for_rent')

        # Pick correct budget band based on purpose
        ranges = BUDGET_RANGES_RENT if is_rent else BUDGET_RANGES_SALE
        budget_min, budget_max = ranges.get(budget_key, (0, 9_999_999_999))

        # ── 1. Fetch exact home listing property inventory ───────────────
        all_properties = get_home_inventory()
        image_map = _get_image_map()

        clean_sector = sector_name.replace('sector', '').replace('&', '').strip().lower()
        sector_specified = bool(clean_sector and clean_sector not in ('islamabad', ''))

        # ── Sector matching helper: checks sector field AND address string ────
        def extract_sector_key(prop):
            """Return the sector identifier from sector field or parsed from address."""
            sec = (prop.get('sector') or '').strip().lower()
            if sec:
                return sec
            addr = (prop.get('address') or '').strip().lower()
            # Extract tokens like f-8, g-10, e-11, dha, bahria, b-17 from address
            import re as _re
            m = _re.search(
                r'\b([a-z]-\d+(?:/\d+)?|dha|bahria\s*town|pwd|cbr|b-17|multi\s*gardens|gulberg|naval\s*anchorage)\b',
                addr
            )
            return m.group(1).strip() if m else addr  # fallback: full address

        def matches_sector(prop):
            """True if the property belongs to the requested sector."""
            if not sector_specified:
                return True  # no sector filter requested
            key     = extract_sector_key(prop)
            title   = (prop.get('title')   or '').lower()
            address = (prop.get('address') or '').lower()
            return (
                clean_sector in key     or
                clean_sector in address or
                clean_sector in title
            )

        def in_budget(prop):
            price = float(prop.get('price_numeric') or 0)
            return price == 0 or (budget_min <= price <= budget_max)

        # ── Purpose filter (rent vs sale) — always hard ───────────────────────
        def purpose_matches(prop):
            status = (prop.get('status') or '').lower()
            title  = (prop.get('title')  or '').lower()
            if is_rent:
                return 'rent' in status or 'for rent' in title or 'rental' in title
            else:
                return 'rent' not in status and 'for rent' not in title

        purpose_filtered = [p for p in all_properties if purpose_matches(p)]

        # ── Sector is the HIGHEST priority ────────────────────────────────────
        # If a sector is specified we NEVER mix in properties from other sectors.
        if sector_specified:
            sector_matched = [p for p in purpose_filtered if matches_sector(p)]

            if not sector_matched:
                # No listings at all for this sector → return honest empty result
                available_sectors = sorted(set(
                    extract_sector_key(p) for p in purpose_filtered if extract_sector_key(p)
                ))
                return jsonify({
                    'success':       True,
                    'property':      None,
                    'properties':    [],
                    'whatsapp':      {
                        'text':  f"Hello! I am looking for {'rental ' if is_rent else ''}properties in sector {sector_name.upper()}, Islamabad. Please share any available options.",
                        'agent': {'name': 'Islamabad Property Desk', 'phone': '+923165756055', 'agency': 'RealEstate AI'}
                    },
                    'total':         0,
                    'match_quality': 'no_sector_listings',
                    'match_label':   f'No {purpose} listings found in {sector_name.upper()}. Available sectors: {", ".join(available_sectors[:8]) if available_sectors else "check back soon"}',
                }), 200

            # Within the sector, prefer budget-matching first, then all sector props
            in_budget_sector = [p for p in sector_matched if in_budget(p)]
            target_props = in_budget_sector if in_budget_sector else sector_matched
            match_quality = 'exact' if in_budget_sector else 'sector_only'

        else:
            # No sector filter → rank all purpose-matching by budget then persona
            target_props  = purpose_filtered
            match_quality = 'all'

        # ── Score and rank within target_props ────────────────────────────────
        def calculate_persona_score(prop):
            score     = 0
            prop_type = (prop.get('property_type') or '').lower()
            price     = float(prop.get('price_numeric') or 0)
            beds      = int(prop.get('beds') or 0)

            # Budget fit (primary sort signal after sector)
            if in_budget(prop):
                score += 40

            # Persona-type fit
            if persona_type == 'luxury' and (price >= 40_000_000 or 'villa' in prop_type or 'penthouse' in prop_type):
                score += 20
            elif persona_type == 'family' and (beds >= 3 or 'villa' in prop_type or 'house' in prop_type):
                score += 20
            elif persona_type == 'investor' and ('plot' in prop_type or 'noc' in str(prop.get('description', '')).lower()):
                score += 20
            elif persona_type == 'first_time' and (price <= 35_000_000 or 'apartment' in prop_type):
                score += 20

            # Beds preference for family
            if persona_type == 'family' and beds >= 4:
                score += 5

            return score

        scored_props  = sorted(
            [(calculate_persona_score(p), p) for p in target_props],
            key=lambda x: x[0], reverse=True
        )
        matched_props = [p for _, p in scored_props]


        # ── 4. Normalise rows for frontend response ───────────────────────
        def normalise(prop):
            pid           = str(prop.get('id', ''))
            price_numeric = prop.get('price_numeric') or 0
            price_display = prop.get('price') or (f"PKR {int(price_numeric):,}" if price_numeric else 'Contact for Price')
            area          = f"{int(prop['area_sqft'])} sqft" if prop.get('area_sqft') else 'N/A'
            status        = prop.get('status') or ('For Rent' if is_rent else 'For Sale')
            img_url       = image_map.get(pid) or prop.get('image_url') or '/static/images/default_property.png'

            return {
                'id':            pid,
                'title':         prop.get('title', 'Islamabad Property'),
                'city':          prop.get('address') or prop.get('sector') or 'Islamabad',
                'sector':        prop.get('sector') or prop.get('address') or 'Islamabad',
                'listing_mode':  'for_rent' if is_rent else 'for_sale',
                'mode':          'for_rent' if is_rent else 'for_sale',
                'status':        status,
                'property_type': prop.get('property_type', 'Residential'),
                'price':         price_display,
                'price_numeric': price_numeric,
                'beds':          prop.get('beds') or 0,
                'baths':         prop.get('baths') or 0,
                'area':          area,
                'area_sqft':     prop.get('area_sqft'),
                'address':       prop.get('address') or 'Islamabad',
                'description':   prop.get('description', ''),
                'amenities':     prop.get('amenities', []),
                'image_url':     img_url,
            }

        normalised = [normalise(p) for p in matched_props[:10]]
        best_match = normalised[0] if normalised else None

        # ── 5. Generate WhatsApp post for best match ──────────────────────
        whatsapp_data = generate_whatsapp_post(best_match, persona_key=persona_type) if best_match else {
            'text':  f"Hello! I am looking for {'rental ' if is_rent else ''}properties in {data.get('city', 'Islamabad')}. Please share available options.",
            'agent': {'name': 'Islamabad Property Desk', 'phone': '+923165756055', 'agency': 'RealEstate AI'}
        }

        match_labels = {
            'exact':       '✅ Exact match — sector & budget',
            'sector_only': '📍 Sector matched — showing all price ranges',
            'budget_only': f'💰 Budget matched — no listings found in {sector_name.upper()}, showing nearby',
            'fallback':    f'🔍 No exact match for {sector_name.upper()} — showing available properties',
        }

        return jsonify({
            'success':      True,
            'property':     best_match,
            'properties':   normalised,
            'whatsapp':     whatsapp_data,
            'total':        len(normalised),
            'match_quality': match_quality,
            'match_label':  match_labels.get(match_quality, ''),
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ── Background WhatsApp Send via Green API (no tab, website stays open) ───────
@persona_bp.route('/api/persona/send-whatsapp-bg', methods=['POST'])
def send_whatsapp_background():
    """
    Silently sends the WhatsApp marketing post to the client's phone via
    Green API — purely server-side, no browser redirect, no new tab.
    """
    try:
        data    = request.json or {}
        phone   = data.get('phone', '').strip()
        message = data.get('message', '').strip()

        if not phone:
            phone = session.get('user_phone', '')

        if not phone:
            return jsonify({'success': False, 'error': 'No phone number provided'}), 400
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400

        result_holder = {}

        def _bg_send():
            result_holder['result'] = _send_via_greenapi(phone, message)

        t = threading.Thread(target=_bg_send, daemon=True)
        t.start()
        t.join(timeout=22)

        result = result_holder.get('result', {'success': False, 'error': 'Timeout'})

        if result.get('success'):
            return jsonify({
                'success': True,
                'message': f'WhatsApp message sent to {phone}',
                'phone':   phone,
            }), 200
        else:
            return jsonify({
                'success':        False,
                'error':          result.get('error', 'Delivery failed'),
                'phone':          phone,
                'setup_required': result.get('setup_required', not bool(GREEN_API_INSTANCE_ID and GREEN_API_TOKEN)),
                'setup_instructions': (
                    'To enable free silent WhatsApp delivery:\n'
                    '1. Go to https://green-api.com and sign up FREE\n'
                    '2. Create a Developer instance (free forever)\n'
                    '3. Scan the QR code with your WhatsApp\n'
                    '4. Copy idInstance and apiTokenInstance\n'
                    '5. Add to .env:\n'
                    '   GREEN_API_INSTANCE_ID=1234567890\n'
                    '   GREEN_API_TOKEN=your_token\n'
                    '6. Restart the server.'
                ) if not (GREEN_API_INSTANCE_ID and GREEN_API_TOKEN) else None,
            }), 200

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(exc)}), 500
