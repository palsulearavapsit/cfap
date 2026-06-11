from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from backend.models import db, Challenge, ChallengeProgress
from backend.routes.auth import login_required

challenges_bp = Blueprint('challenges', __name__, url_prefix='/challenges')

@challenges_bp.route('/', methods=['GET'])
@login_required
def get_challenges():
    challenges = Challenge.query.order_by(Challenge.id.asc()).all()
    output = []
    for chal in challenges:
        output.append({
            "id": chal.id,
            "title": chal.title,
            "description": chal.description,
            "difficulty": chal.difficulty,
            "points": chal.points
        })
    return jsonify(output), 200

@challenges_bp.route('/active', methods=['GET'])
@login_required
def get_active_challenges():
    user = request.current_user
    progresses = ChallengeProgress.query.filter_by(user_id=user.id).order_by(ChallengeProgress.start_date.desc()).all()
    output = []
    for prog in progresses:
        # Fetch associated challenge info
        chal = Challenge.query.get(prog.challenge_id)
        output.append({
            "id": prog.id,
            "user_id": prog.user_id,
            "challenge_id": prog.challenge_id,
            "start_date": prog.start_date.isoformat(),
            "end_date": prog.end_date.isoformat(),
            "completion_status": prog.completion_status,
            "points_earned": prog.points_earned,
            "proof_text": prog.proof_text,
            "challenge": {
                "id": chal.id,
                "title": chal.title,
                "description": chal.description,
                "difficulty": chal.difficulty,
                "points": chal.points
            } if chal else None
        })
    return jsonify(output), 200

@challenges_bp.route('/join', methods=['POST'])
@login_required
def join_challenge():
    user = request.current_user
    data = request.get_json() or {}
    challenge_id = data.get("challenge_id")

    if not challenge_id:
        return jsonify({"detail": "challenge_id is required"}), 400

    challenge = Challenge.query.get(challenge_id)
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

    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=7) # Standard challenge length of 7 days

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

    return jsonify({
        "id": new_progress.id,
        "user_id": new_progress.user_id,
        "challenge_id": new_progress.challenge_id,
        "start_date": new_progress.start_date.isoformat(),
        "end_date": new_progress.end_date.isoformat(),
        "completion_status": new_progress.completion_status,
        "points_earned": new_progress.points_earned,
        "proof_text": None,
        "challenge": {
            "id": challenge.id,
            "title": challenge.title,
            "description": challenge.description,
            "difficulty": challenge.difficulty,
            "points": challenge.points
        }
    }), 201

@challenges_bp.route('/<int:progress_id>/complete', methods=['POST'])
@login_required
def complete_challenge(progress_id):
    user = request.current_user
    progress = ChallengeProgress.query.filter_by(id=progress_id, user_id=user.id).first()

    if not progress:
        return jsonify({"detail": "Challenge progress record not found"}), 404

    if progress.completion_status != "in_progress":
        return jsonify({"detail": f"Challenge is already {progress.completion_status}"}), 400

    challenge = Challenge.query.get(progress.challenge_id)
    if not challenge:
        return jsonify({"detail": "Associated challenge not found"}), 404

    data = request.get_json(silent=True) or {}
    proof_text = data.get("proof_text", "").strip()

    progress.completion_status = "completed"
    progress.points_earned = challenge.points
    progress.proof_text = proof_text if proof_text else None
    db.session.commit()

    return jsonify({
        "id": progress.id,
        "user_id": progress.user_id,
        "challenge_id": progress.challenge_id,
        "start_date": progress.start_date.isoformat(),
        "end_date": progress.end_date.isoformat(),
        "completion_status": progress.completion_status,
        "points_earned": progress.points_earned,
        "proof_text": progress.proof_text,
        "challenge": {
            "id": challenge.id,
            "title": challenge.title,
            "description": challenge.description,
            "difficulty": challenge.difficulty,
            "points": challenge.points
        }
    }), 200
