from flask import Blueprint, request, jsonify, Response
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from backend.models import db, Challenge, ChallengeProgress
from backend.routes.auth import login_required
from typing import Any, List

challenges_bp = Blueprint('challenges', __name__, url_prefix='/challenges')

@challenges_bp.route('/', methods=['GET'])
@login_required
def get_challenges() -> Response:
    """Returns a list of all seeded sustainability challenges in ascending order of ID."""
    challenges: List[Challenge] = Challenge.query.order_by(Challenge.id.asc()).all()
    # Action 3: Serialize output using to_dict() model representation
    return jsonify([chal.to_dict() for chal in challenges]), 200

@challenges_bp.route('/active', methods=['GET'])
@login_required
def get_active_challenges() -> Response:
    """Returns user challenge enrollment and progress records, eager-loading related metadata."""
    user = request.current_user # type: ignore
    progresses: List[ChallengeProgress] = (ChallengeProgress.query
                                           .filter_by(user_id=user.id)
                                           .options(joinedload(ChallengeProgress.challenge))
                                           .order_by(ChallengeProgress.start_date.desc())
                                           .all())
    # Action 3: Serialize output using to_dict() model representation
    return jsonify([prog.to_dict() for prog in progresses]), 200

@challenges_bp.route('/join', methods=['POST'])
@login_required
def join_challenge() -> Response:
    """Joins a sustainability challenge, validating input types and double-joining states."""
    user = request.current_user # type: ignore
    data: dict = request.get_json() or {}
    challenge_id: Any = data.get("challenge_id")

    if not challenge_id:
        return jsonify({"detail": "challenge_id is required"}), 400

    # Action 6: Enforce strict type validation
    if not isinstance(challenge_id, int):
        return jsonify({"detail": "challenge_id must be an integer"}), 400

    challenge = db.session.get(Challenge, challenge_id)
    if not challenge:
        return jsonify({"detail": "Challenge not found"}), 404

    # Verify if user has already joined and is in_progress
    existing = ChallengeProgress.query.filter_by(
        user_id=user.id,
        challenge_id=challenge_id,
        completion_status="in_progress"
    ).first()
    
    if existing:
        return jsonify({"detail": "You are already participating in this challenge"}), 400

    start_date: datetime = datetime.utcnow()
    end_date: datetime = start_date + timedelta(days=7) # Standard challenge length of 7 days

    new_progress = ChallengeProgress(
        user_id=user.id,
        challenge_id=challenge_id,
        start_date=start_date,
        end_date=end_date,
        completion_status="in_progress",
        points_earned=0
    )
    
    db.session.add(new_progress)
    db.session.commit()

    # Action 3: Serialize output using to_dict() model representation
    return jsonify(new_progress.to_dict()), 201

@challenges_bp.route('/<int:progress_id>/complete', methods=['POST'])
@login_required
def complete_challenge(progress_id: int) -> Response:
    """Completes an in-progress challenge with validated text proof, awarding points."""
    user = request.current_user # type: ignore
    progress = ChallengeProgress.query.filter_by(id=progress_id, user_id=user.id).first()

    if not progress:
        return jsonify({"detail": "Challenge progress record not found"}), 404

    if progress.completion_status != "in_progress":
        return jsonify({"detail": f"Challenge is already {progress.completion_status}"}), 400

    challenge = db.session.get(Challenge, progress.challenge_id)
    if not challenge:
        return jsonify({"detail": "Associated challenge not found"}), 404

    data: dict = request.get_json(silent=True) or {}
    raw_proof: Any = data.get("proof_text", "")

    # Action 6: Enforce strict type validation
    if not isinstance(raw_proof, str):
        return jsonify({"detail": "Proof text must be a string type"}), 400

    proof_text: str = raw_proof.strip()

    if len(proof_text) > 1000:
        return jsonify({"detail": "Proof text cannot exceed 1000 characters"}), 400

    progress.completion_status = "completed"
    progress.points_earned = challenge.points
    progress.proof_text = proof_text if proof_text else None
    db.session.commit()

    # Action 3: Serialize output using to_dict() model representation
    return jsonify(progress.to_dict()), 200
