import os
import json
import subprocess
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, send_from_directory, send_file, Response, request, session, redirect, url_for

# Load .env variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional — env vars may be set at system level

from routes.properties import properties_bp
from routes.persona import persona_bp
from routes.marketing import marketing_bp
from routes.ads import ads_bp
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.brand import brand_bp

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "realestate_ai_secret_key_2026")

app.register_blueprint(properties_bp)
app.register_blueprint(persona_bp)
app.register_blueprint(marketing_bp)
app.register_blueprint(ads_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(brand_bp)


# ── ROLE-BASED ACCESS CONTROL DECORATOR ─────────────────────────────────────
def admin_required(f):
    """Decorator: blocks non-admin users from accessing a route.
    - For page routes (GET HTML): redirects to home with ?access=denied
    - For API routes: returns 403 JSON error
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        is_api  = request.path.startswith('/api/')

        if not user_id and not user_email:
            if is_api:
                return jsonify({'error': 'Authentication required.'}), 401
            return redirect('/?access=denied&reason=login')

        # Lazy import to avoid circular
        from auth_db import get_user_by_id, get_user_by_email
        user = get_user_by_id(user_id) if user_id else None
        if not user and user_email:
            user = get_user_by_email(user_email)
            if user:
                session['user_id'] = user['id']

        if not user or user.get('role') != 'admin':
            if is_api:
                return jsonify({'error': 'Admin access required. This feature is not available for your account.'}), 403
            return redirect('/?access=denied&reason=role')

        return f(*args, **kwargs)
    return decorated


@app.route('/api/auth/config', methods=['GET'])
def get_auth_config():
    """Expose public auth config (e.g. Google Client ID) to the frontend."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    has_google = bool(client_id and client_id != "REPLACE_WITH_YOUR_GOOGLE_CLIENT_ID")
    return jsonify({
        "google_client_id": client_id if has_google else None,
        "google_configured": has_google
    })


@app.route('/')
def index():
    return send_from_directory('.', 'property.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/modules/data/<path:filename>')
def serve_modules_data(filename):
    import mimetypes
    # Candidate paths in priority order:
    # 1. /tmp/ — writable on Vercel, freshly generated after scrape
    # 2. Absolute path relative to this file — committed static copy
    # 3. CWD-relative fallback
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join('/tmp', filename),
        os.path.join(_this_dir, 'modules', 'data', filename),
        os.path.join(os.getcwd(), 'modules', 'data', filename),
        os.path.join(_this_dir, 'data', filename),
    ]
    for path in candidates:
        if os.path.isfile(path):
            mime = mimetypes.guess_type(path)[0] or 'text/html'
            return send_file(os.path.abspath(path), mimetype=mime)

    # No report exists yet — return a helpful placeholder page
    if filename.endswith('.html'):
        placeholder = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>No Report Yet</title>
<style>
  body{margin:0;background:#090d16;color:#94a3b8;font-family:'Segoe UI',sans-serif;
       display:flex;align-items:center;justify-content:center;min-height:100vh;text-align:center}
  .box{padding:40px;background:#111827;border:1px solid #1e293b;border-radius:16px;max-width:460px}
  h2{color:#f1f5f9;margin-bottom:12px;font-size:1.3rem}
  p{margin:0;font-size:.95rem;line-height:1.6}
  .btn{display:inline-block;margin-top:20px;padding:10px 24px;
       background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;
       border-radius:8px;font-size:.9rem;text-decoration:none}
</style>
</head>
<body>
<div class="box">
  <h2>📊 No Report Generated Yet</h2>
  <p>Click <strong>Run Real-Time Scrape</strong> above to generate your competitor intelligence report.</p>
  <a class="btn" href="javascript:window.parent.document.getElementById('run-scrape-btn')?.click()">
    Generate Report
  </a>
</div>
</body>
</html>"""
        return placeholder, 200, {'Content-Type': 'text/html; charset=utf-8'}

    return "File not found", 404

@app.route('/competitor')
@admin_required
def competitor():
    return send_from_directory('.', 'competitor.html')

@app.route('/marketing_report')
@admin_required
def marketing_report():
    return send_from_directory('.', 'marketing_report.html')

@app.route('/chat_assistant')
@admin_required
def chat_assistant():
    return send_from_directory('.', 'chat_assistant.html')

@app.route('/brand_memory')
@admin_required
def brand_memory():
    return send_from_directory('.', 'brand_memory.html')

@app.route('/ad_engine')
@admin_required
def ad_engine():
    return send_from_directory('.', 'ad_engine.html')

@app.route('/persona')
@admin_required
def persona_page():
    return send_from_directory('.', 'persona_app.html')

@app.route('/api/run_competitor_engine', methods=['GET', 'POST'])
@admin_required
def run_engine():
    import queue, threading

    # ── Vercel: subprocess is blocked — call the module directly ─────────────
    IS_VERCEL = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))

    if IS_VERCEL:
        def generate():
            import io, sys
            yield "data: 0% — Scraper starting…\n\n"

            output_q = queue.Queue()

            def _run_engine_in_thread():
                """Run competitor engine in-process, capturing print() output."""
                import importlib.util, sys, io
                # Redirect stdout so print() calls become SSE messages
                old_stdout = sys.stdout
                class _LineCapture(io.TextIOBase):
                    def write(self, text):
                        if text.strip():
                            output_q.put(text.rstrip('\r\n'))
                        return len(text)
                sys.stdout = _LineCapture()
                try:
                    # Load competitor_engine as a module without re-importing cached version
                    spec = importlib.util.spec_from_file_location(
                        "competitor_engine",
                        os.path.abspath(os.path.join('modules', 'competitor_engine.py'))
                    )
                    mod = importlib.util.module_from_spec(spec)
                    old_cwd = os.getcwd()
                    os.chdir(os.path.abspath('modules'))
                    try:
                        spec.loader.exec_module(mod)
                    finally:
                        os.chdir(old_cwd)
                except SystemExit:
                    pass  # competitor_engine calls sys.exit(1) on failure — safe to swallow
                except Exception as exc:
                    output_q.put(f"ERROR: {exc}")
                finally:
                    sys.stdout = old_stdout
                    output_q.put(None)  # sentinel

            t = threading.Thread(target=_run_engine_in_thread, daemon=True)
            t.start()

            while True:
                try:
                    line = output_q.get(timeout=2.0)
                except queue.Empty:
                    if not t.is_alive():
                        break
                    yield ": keepalive\n\n"
                    continue
                if line is None:
                    break
                yield f"data: {line}\n\n"

            if t.is_alive():
                t.join(timeout=5)
            yield "data: [DONE]\n\n"

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            },
        )

    # ── Local dev: original subprocess approach (unchanged) ──────────────────
    script_path = os.path.abspath(os.path.join('modules', 'competitor_engine.py'))
    cwd_path    = os.path.abspath('modules')

    def generate():
        # Immediate heartbeat so browser knows the connection is open
        yield "data: 0% — Scraper starting…\n\n"

        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'

        process = subprocess.Popen(
            ['python', '-u', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            cwd=cwd_path,
            env=env,
        )

        q = queue.Queue()

        def reader():
            """Background thread: push every raw line into the queue."""
            for raw in iter(process.stdout.readline, b''):
                q.put(raw)
            process.stdout.close()
            q.put(None)   # sentinel

        t = threading.Thread(target=reader, daemon=True)
        t.start()

        while True:
            try:
                raw = q.get(timeout=2.0)   # wait up to 2 s for a line
            except queue.Empty:
                # No output yet but process still running → keepalive
                if process.poll() is not None:
                    break
                yield ": keepalive\n\n"
                continue

            if raw is None:   # sentinel — reader thread is done
                break

            text = raw.decode('utf-8', errors='replace').rstrip('\r\n')
            if text:
                yield f"data: {text}\n\n"

        process.wait()
        if process.returncode == 0:
            yield "data: [DONE]\n\n"
        else:
            yield "data: [ERROR]\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@app.route('/api/scrape_html_file', methods=['POST'])
@admin_required
def scrape_html_file():
    """
    Upload a locally saved Zameen.com HTML file and scrape it.
    Form fields:
      - file   : the .html file (multipart/form-data)
      - city   : optional city label string
      - save   : optional 'true' to append results to data/zameen_listings.csv
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    f = request.files['file']
    if not f.filename.lower().endswith('.html'):
        return jsonify({'error': 'Only .html files are accepted'}), 400

    city_label = request.form.get('city', 'Islamabad').strip() or 'Islamabad'
    should_save = request.form.get('save', 'true').lower() == 'true'

    # Write to a temp file so scrape_from_html_file() can read it normally
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='wb') as tmp:
        f.save(tmp)
        tmp_path = tmp.name

    try:
        from modules.competitor_engine import scrape_from_html_file, save_to_csv
        listings = scrape_from_html_file(tmp_path, city_label=city_label)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    if not listings:
        return jsonify({'success': False, 'error': 'No listings found in the HTML file.'}), 200

    if should_save:
        save_to_csv(listings, filename='data/zameen_listings.csv')

    return jsonify({
        'success':  True,
        'count':    len(listings),
        'city':     city_label,
        'preview':  listings[:5],   # first 5 for quick review
        'saved':    should_save,
    }), 200


IMAGES_DIR   = os.path.join('static', 'images')
IMAGES_MAP   = os.path.join('static', 'images', 'property_images.json')
os.makedirs(IMAGES_DIR, exist_ok=True)

ALLOWED_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTS

def _load_map():
    if os.path.exists(IMAGES_MAP):
        with open(IMAGES_MAP) as f:
            return json.load(f)
    return {}

def _save_map(m):
    with open(IMAGES_MAP, 'w') as f:
        json.dump(m, f, indent=2)

@app.route('/api/property_images', methods=['GET'])
def get_property_images():
    """Return the property_id → image_url mapping."""
    return jsonify(_load_map())

@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    """Upload an image for a specific property.
    Supports multiple images per property — stored as a list.
    Form fields: property_id (string), file (image).
    """
    property_id = request.form.get('property_id', '').strip()
    if not property_id:
        return jsonify({'error': 'property_id required'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not _allowed(f.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    m = _load_map()

    # Count existing images for this property to generate unique filename index
    existing = m.get(property_id, [])
    if isinstance(existing, str):
        existing = [existing]  # migrate old single-string format
    idx = len(existing) + 1

    ext      = f.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(f'property_{property_id}_{idx}.{ext}')
    filepath = os.path.join(IMAGES_DIR, filename)
    f.save(filepath)

    url = f'/static/images/{filename}'
    existing.append(url)
    m[property_id] = existing
    _save_map(m)

    return jsonify({'url': url, 'all_images': existing}), 200


@app.route('/api/delete_image', methods=['POST'])
def delete_image():
    """Remove a specific image URL from a property's image list."""
    data        = request.get_json(silent=True) or {}
    property_id = data.get('property_id', '').strip()
    image_url   = data.get('image_url', '').strip()
    if not property_id or not image_url:
        return jsonify({'error': 'property_id and image_url required'}), 400

    m        = _load_map()
    existing = m.get(property_id, [])
    if isinstance(existing, str):
        existing = [existing]
    existing = [u for u in existing if u != image_url]
    m[property_id] = existing
    _save_map(m)

    # Optionally delete the file from disk
    try:
        rel = image_url.lstrip('/')
        path = os.path.join(IMAGES_DIR, os.path.basename(rel))
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

    return jsonify({'status': 'deleted', 'all_images': existing}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
