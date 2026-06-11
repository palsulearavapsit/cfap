from flask import Blueprint, request, jsonify, Response, current_app
from backend.models import db, Recommendation
from backend.routes.auth import login_required
from typing import List

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')

@recommendations_bp.route('/status', methods=['GET'])
def get_recommendations_status() -> Response:
    """Returns whether the Gemini API key is currently configured on the server."""
    has_key: bool = bool(current_app.config.get('GEMINI_API_KEY'))
    return jsonify({"gemini_configured": has_key}), 200

@recommendations_bp.route('/', methods=['GET'])
@login_required
def get_recommendations() -> Response:
    """Returns a list of all personalized sustainability recommendations for the user."""
    user = request.current_user # type: ignore
    recs: List[Recommendation] = Recommendation.query.filter_by(user_id=user.id).order_by(Recommendation.created_at.desc()).all()
    # Action 3: Serialize recommendations list using model to_dict representation
    return jsonify([r.to_dict() for r in recs]), 200

@recommendations_bp.route('/<int:rec_id>/complete', methods=['PATCH'])
@login_required
def toggle_recommendation(rec_id: int) -> Response:
    """Toggles the completion status checkbox of a personalized recommendation."""
    user = request.current_user # type: ignore
    rec = Recommendation.query.filter_by(id=rec_id, user_id=user.id).first()

    if not rec:
        return jsonify({"detail": "Recommendation not found"}), 404

    try:
        # Toggle the boolean completion status
        rec.is_completed = not rec.is_completed
        db.session.commit()
    except Exception as db_err:
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f"Toggle recommendation database error: {str(db_err)}", exc_info=True)
        return jsonify({"detail": "Database operation failed. Please try again later."}), 500

    # Action 3: Serialize output using to_dict() model representation
    return jsonify(rec.to_dict()), 200
