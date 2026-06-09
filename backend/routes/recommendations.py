from flask import Blueprint, request, jsonify
from backend.models import db, Recommendation
from backend.routes.auth import login_required

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')

@recommendations_bp.route('/', methods=['GET'])
@login_required
def get_recommendations():
    user = request.current_user
    recs = Recommendation.query.filter_by(user_id=user.id).order_by(Recommendation.created_at.desc()).all()
    output = []
    for r in recs:
        output.append({
            "id": r.id,
            "user_id": r.user_id,
            "title": r.title,
            "description": r.description,
            "difficulty": r.difficulty,
            "expected_reduction": r.expected_reduction,
            "estimated_savings": r.estimated_savings,
            "is_completed": r.is_completed,
            "created_at": r.created_at.isoformat()
        })
    return jsonify(output), 200

@recommendations_bp.route('/<int:rec_id>/complete', methods=['PATCH'])
@login_required
def toggle_recommendation(rec_id):
    user = request.current_user
    rec = Recommendation.query.filter_by(id=rec_id, user_id=user.id).first()

    if not rec:
        return jsonify({"detail": "Recommendation not found"}), 404

    # Toggle the boolean completion status
    rec.is_completed = not rec.is_completed
    db.session.commit()

    return jsonify({
        "id": rec.id,
        "user_id": rec.user_id,
        "title": rec.title,
        "description": rec.description,
        "difficulty": rec.difficulty,
        "expected_reduction": rec.expected_reduction,
        "estimated_savings": rec.estimated_savings,
        "is_completed": rec.is_completed,
        "created_at": rec.created_at.isoformat()
    }), 200
