"""
routes/marketing.py — Marketing Report Blueprint
Exposes all API endpoints needed by the marketing_report.html frontend.

Endpoints:
  POST /api/reviews/submit          — submit a new review
  GET  /api/reviews                 — get all reviews + stats
  GET  /api/marketing/report        — run full analysis + AI insights (SSE stream)
  GET  /api/marketing/health        — lightweight health scores only
  POST /api/listings/like           — toggle like on a listing
  GET  /api/listings/likes          — get like counts for all listings
  GET  /api/listings/<id>/reviews   — get reviews for a specific listing
  POST /api/listings/review         — submit a review for a specific listing
"""

import json
import sys
import os

from flask import Blueprint, request, jsonify, Response, session

# Resolve project root so we can import modules/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.marketing_reports.reviews import (
    submit_review, get_all_reviews, compute_review_stats,
)
from modules.marketing_reports.aggregator import run_full_analysis
from modules.marketing_reports.insights_engine import generate_insights

marketing_bp = Blueprint('marketing', __name__)


def _sse(event: str, data: str) -> str:
    """Format a Server-Sent Event message."""
    return f"event: {event}\ndata: {data}\n\n"



# ---------------------------------------------------------------------------
# POST /api/reviews/submit
# ---------------------------------------------------------------------------

@marketing_bp.route('/api/reviews/submit', methods=['POST'])
def api_submit_review():
    """
    Body (JSON):
      { "reviewer_name": str, "rating": int (1–5),
        "comment": str, "property_id": str (optional) }
    """
    data = request.json or {}

    name    = (data.get('reviewer_name') or '').strip()
    rating  = data.get('rating')
    comment = (data.get('comment') or '').strip()
    prop_id = data.get('property_id')

    if not name:
        return jsonify({'success': False, 'error': 'reviewer_name is required'}), 400
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({'success': False, 'error': 'rating must be an integer 1–5'}), 400
    if not comment:
        return jsonify({'success': False, 'error': 'comment is required'}), 400

    result = submit_review(
        reviewer_name=name,
        rating=rating,
        comment=comment,
        source='website',
        property_id=prop_id,
    )

    status = 201 if result.get('success') else 500
    return jsonify(result), status


# ---------------------------------------------------------------------------
# GET /api/reviews
# ---------------------------------------------------------------------------

@marketing_bp.route('/api/reviews', methods=['GET'])
def api_get_reviews():
    """Returns all reviews + computed stats."""
    reviews = get_all_reviews()
    stats   = compute_review_stats(reviews)
    return jsonify({
        'reviews': reviews,
        'stats':   stats,
    }), 200


# ---------------------------------------------------------------------------
# GET /api/marketing/health   (fast, no AI)
# ---------------------------------------------------------------------------

@marketing_bp.route('/api/marketing/health', methods=['GET'])
def api_marketing_health():
    """
    Lightweight endpoint: returns health scores, engagement metrics, and AI insights.
    Used on page load to populate metrics immediately.
    """
    try:
        reviews = get_all_reviews()
        stats   = compute_review_stats(reviews)
        from auth_db import get_all_listing_engagement
        engagement = get_all_listing_engagement()
        merged = {'reviews': stats, 'engagement': engagement}
        insights = generate_insights(merged)
        return jsonify({
            'success':      True,
            'avg_rating':   stats['avg_rating'],
            'total':        stats['total'],
            'distribution': stats['distribution'],
            'engagement':   engagement,
            'insights':     insights,
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# GET /api/marketing/report   (SSE-streamed full analysis)
# ---------------------------------------------------------------------------

@marketing_bp.route('/api/marketing/report', methods=['GET'])
def api_marketing_report():
    """
    Runs the full pipeline (reviews → scan → aggregate → AI insights → engagement)
    and streams progress as Server-Sent Events so the UI shows live updates.
    Final SSE event contains the full JSON payload tagged as [REPORT].
    """

    def generate():
        try:
            yield _sse("step", "🔍 Fetching customer reviews…")

            reviews = get_all_reviews()
            stats   = compute_review_stats(reviews)
            yield _sse("step", f"✅ {stats['total']} reviews loaded (avg {stats['avg_rating']}/5)")

            yield _sse("step", "🌐 Scanning website pages for issues…")
            from modules.marketing_reports.website_scanner import scan_website
            website_data = scan_website()
            yield _sse("step",
                f"✅ Scanned {website_data['total_pages_scanned']} pages, "
                f"found {website_data['total_issues']} issues"
            )

            yield _sse("step", "🔗 Correlating review signals with site data…")
            from modules.marketing_reports.aggregator import run_full_analysis
            # Re-use already-fetched data instead of calling run_full_analysis
            # (avoids duplicate DB calls)
            from modules.marketing_reports.aggregator import _compute_health_score
            health  = _compute_health_score(stats, website_data)
            summary = {
                'review_count':      stats['total'],
                'avg_rating':        stats['avg_rating'],
                'total_site_issues': website_data['total_issues'],
                'avg_load_time_ms':  website_data.get('avg_load_time_ms'),
                'cross_signals':     [],
                'overall_health':    health,
            }
            yield _sse("step", "❤️ Compiling listing engagement metrics…")
            from auth_db import get_all_listing_engagement
            engagement = get_all_listing_engagement()
            yield _sse("step",
                f"✅ {engagement['total_likes']} total likes · "
                f"{engagement['total_listing_reviews']} listing reviews"
            )

            merged = {'reviews': stats, 'website': website_data, 'summary': summary, 'engagement': engagement}
            yield _sse("step", "✅ Cross-signal correlation complete")

            yield _sse("step", "🤖 Running AI insights engine…")
            insights = generate_insights(merged)
            mode = "Gemini LLM" if insights.get("generated_by") == "gemini" else "Rule Engine"
            yield _sse("step", f"✅ Insights generated via {mode}")


            # Build final payload
            payload = {
                'reviews':    stats,
                'website':    website_data,
                'summary':    summary,
                'insights':   insights,
                'engagement': engagement,
            }

            yield _sse("report", json.dumps(payload))
            yield _sse("done",   "Report complete")

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield _sse("error", str(e))

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control':    'no-cache',
            'X-Accel-Buffering':'no',
            'Connection':       'keep-alive',
        },
    )


# ---------------------------------------------------------------------------
# POST /api/listings/like  — toggle heart like on a listing
# ---------------------------------------------------------------------------

@marketing_bp.route('/api/listings/like', methods=['POST'])
def api_toggle_listing_like():
    """Body: { "property_id": str }. Saves user identity when logged in."""
    data = request.json or {}
    property_id = (data.get('property_id') or '').strip()
    if not property_id:
        return jsonify({'success': False, 'error': 'property_id required'}), 400

    # Use logged-in user_id as session key when available (most reliable)
    user_id    = session.get('user_id')
    user_email = session.get('user_email')
    session_key = user_id or request.headers.get('X-Session-Key', '') or request.remote_addr

    from auth_db import toggle_listing_like
    result = toggle_listing_like(property_id, session_key, user_id=user_id, user_email=user_email)
    return jsonify({'success': True, **result}), 200


# ---------------------------------------------------------------------------
# GET /api/listings/likes  — get all like counts + user's liked set
# ---------------------------------------------------------------------------

@marketing_bp.route('/api/listings/likes', methods=['GET'])
def api_get_listing_likes():
    """Returns {counts: {prop_id: n}, user_liked: [prop_ids]}."""
    session_key = session.get('user_id') or request.headers.get('X-Session-Key', '') or request.remote_addr
    from auth_db import get_listing_likes, get_user_liked_properties
    counts     = get_listing_likes()
    user_liked = get_user_liked_properties(session_key)
    return jsonify({'counts': counts, 'user_liked': user_liked}), 200


# ---------------------------------------------------------------------------
# GET /api/listings/<property_id>/reviews  — get reviews for a listing
# ---------------------------------------------------------------------------

@marketing_bp.route('/api/listings/<property_id>/reviews', methods=['GET'])
def api_get_listing_reviews(property_id):
    from auth_db import get_listing_reviews
    reviews = get_listing_reviews(property_id)
    return jsonify({'reviews': reviews}), 200


# ---------------------------------------------------------------------------
# POST /api/listings/review  — submit a review for a specific listing
# ---------------------------------------------------------------------------

@marketing_bp.route('/api/listings/review', methods=['POST'])
def api_submit_listing_review():
    """Body: { property_id, reviewer_name, rating (1-5), comment }.
    If the user is logged in, their account credentials are saved automatically."""
    data = request.json or {}
    property_id   = (data.get('property_id') or '').strip()
    rating        = data.get('rating')
    comment       = (data.get('comment') or '').strip()

    # Auto-fill reviewer_name from logged-in session when not provided
    user_id    = session.get('user_id')
    user_email = session.get('user_email')
    user_name  = session.get('user_name', '')
    reviewer_name = (data.get('reviewer_name') or user_name or '').strip()

    if not property_id:
        return jsonify({'success': False, 'error': 'property_id required'}), 400
    if not reviewer_name:
        return jsonify({'success': False, 'error': 'reviewer_name required'}), 400
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({'success': False, 'error': 'rating must be 1–5'}), 400
    if not comment:
        return jsonify({'success': False, 'error': 'comment required'}), 400

    from auth_db import submit_listing_review
    result = submit_listing_review(
        property_id, reviewer_name, rating, comment,
        user_id=user_id, user_email=user_email
    )
    return jsonify(result), 201 if result.get('success') else 500


def _sse_end_sentinel(): pass  # end of file marker
