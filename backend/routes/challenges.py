import logging
from datetime import datetime, timedelta
from typing import Any, List

from flask import Blueprint, Response, request
from sqlalchemy.orm import joinedload

from backend.constants import CHALLENGE_DURATION_DAYS, DEFAULT_CHALLENGE_DURATION_DAYS
from backend.models import Challenge, ChallengeProgress, db
from backend.routes.auth import login_required
from backend.utils import send_response

logger = logging.getLogger("ecotrack.challenges")

challenges_bp = Blueprint("challenges", __name__, url_prefix="/challenges")

# Static challenges list in-memory cache to save database queries
challenges_cache = None


@challenges_bp.route("/", methods=["GET"])
@login_required
def get_challenges() -> Response:
    """Returns a list of all seeded sustainability challenges in ascending order of ID."""
    global challenges_cache
    if challenges_cache is None:
        challenges: List[Challenge] = Challenge.query.order_by(Challenge.id.asc()).all()
        challenges_cache = [chal.to_dict() for chal in challenges]
    return send_response(challenges_cache, 200)


@challenges_bp.route("/search", methods=["GET"])
@login_required
def search_challenges() -> Response:
    """Search challenges by query string keyword using safe parameterized filter queries."""
    q: str = request.args.get("q", "").strip()
    difficulty: str = request.args.get("difficulty", "").strip()

    query = Challenge.query
    if q:
        query = query.filter(
            Challenge.title.ilike(f"%{q}%") | Challenge.description.ilike(f"%{q}%")
        )
    if difficulty:
        query = query.filter(Challenge.difficulty.ilike(difficulty))

    results: List[Challenge] = query.order_by(Challenge.id.asc()).all()
    return send_response([r.to_dict() for r in results], 200)


@challenges_bp.route("/active", methods=["GET"])
@login_required
def get_active_challenges() -> Response:
    """Returns user challenge enrollment and progress records, eager-loading related metadata."""
    user = request.current_user  # type: ignore
    progresses: List[ChallengeProgress] = (
        ChallengeProgress.query.filter_by(user_id=user.id)
        .options(joinedload(ChallengeProgress.challenge))
        .order_by(ChallengeProgress.start_date.desc())
        .all()
    )
    # Action 3: Serialize output using to_dict() model representation
    return send_response([prog.to_dict() for prog in progresses], 200)


@challenges_bp.route("/join", methods=["POST"])
@login_required
def join_challenge() -> Response:
    """Joins a sustainability challenge, validating input types and double-joining states."""
    user = request.current_user  # type: ignore
    data: dict = request.get_json() or {}
    challenge_id: Any = data.get("challenge_id")

    if not challenge_id:
        return send_response({"detail": "challenge_id is required"}, 400)

    # Action 6: Enforce strict type validation
    if not isinstance(challenge_id, int):
        return send_response({"detail": "challenge_id must be an integer"}, 400)

    challenge = db.session.get(Challenge, challenge_id)
    if not challenge:
        return send_response({"detail": "Challenge not found"}, 404)

    # Verify if user has already joined and is in_progress
    existing = ChallengeProgress.query.filter_by(
        user_id=user.id, challenge_id=challenge_id, completion_status="in_progress"
    ).first()

    if existing:
        return send_response(
            {"detail": "You are already participating in this challenge"}, 400
        )

    start_date: datetime = datetime.utcnow()
    # Use dynamic duration based on difficulty level (Item 17)
    duration_days: int = CHALLENGE_DURATION_DAYS.get(
        challenge.difficulty, DEFAULT_CHALLENGE_DURATION_DAYS
    )
    end_date: datetime = start_date + timedelta(days=duration_days)

    new_progress = ChallengeProgress(
        user_id=user.id,
        challenge_id=challenge_id,
        start_date=start_date,
        end_date=end_date,
        completion_status="in_progress",
        points_earned=0,
    )

    try:
        db.session.add(new_progress)
        db.session.commit()
    except Exception as db_err:
        db.session.rollback()
        logger.error(f"Join challenge database error: {str(db_err)}", exc_info=True)
        return send_response(
            {"detail": "Database operation failed. Please try again later."}, 500
        )

    # Action 3: Serialize output using to_dict() model representation
    return send_response(new_progress.to_dict(), 201)


@challenges_bp.route("/<int:progress_id>/complete", methods=["POST"])
@login_required
def complete_challenge(progress_id: int) -> Response:
    """Completes an in-progress challenge with validated text proof, awarding points."""
    user = request.current_user  # type: ignore
    progress = ChallengeProgress.query.filter_by(
        id=progress_id, user_id=user.id
    ).first()

    if not progress:
        return send_response({"detail": "Challenge progress record not found"}, 404)

    if progress.completion_status != "in_progress":
        return send_response(
            {"detail": f"Challenge is already {progress.completion_status}"}, 400
        )

    challenge = db.session.get(Challenge, progress.challenge_id)
    if not challenge:
        return send_response({"detail": "Associated challenge not found"}, 404)

    data: dict = request.get_json(silent=True) or {}
    raw_proof: Any = data.get("proof_text", "")
    raw_image: Any = data.get("proof_image", "")

    # Action 6: Enforce strict type validation
    if not isinstance(raw_proof, str):
        return send_response({"detail": "Proof text must be a string type"}, 400)

    if not isinstance(raw_image, str):
        return send_response({"detail": "Proof image must be a string type"}, 400)

    proof_text: str = raw_proof.strip()
    proof_image: str = raw_image.strip()

    if len(proof_text) > 1000:
        return send_response(
            {"detail": "Proof text cannot exceed 1000 characters"}, 400
        )

    if len(proof_image) > 1.5 * 1024 * 1024:
        return send_response({"detail": "Proof image size exceeds maximum limits"}, 400)

    # HTML Sanitizer regex to prevent stored Cross-Site Scripting (XSS) at backend layer
    import re

    proof_text = re.sub(r"<[^>]*>", "", proof_text)

    try:
        progress.completion_status = "completed"
        progress.points_earned = challenge.points
        progress.proof_text = proof_text if proof_text else None
        progress.proof_image = proof_image if proof_image else None
        db.session.commit()
    except Exception as db_err:
        db.session.rollback()
        logger.error(f"Complete challenge database error: {str(db_err)}", exc_info=True)
        return send_response(
            {"detail": "Database operation failed. Please try again later."}, 500
        )

    # Action 3: Serialize output using to_dict() model representation
    return send_response(progress.to_dict(), 200)
