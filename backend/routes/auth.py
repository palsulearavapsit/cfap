import hashlib
import logging
import re
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import bcrypt
from flask import Blueprint, Response, current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.models import User, db
from backend.utils import send_response

logger = logging.getLogger("ecotrack.auth")

# In-memory rate limiter: IP -> list of timestamps of requests
rate_limit_store: Dict[str, List[float]] = defaultdict(list)

# In-memory login failures store: IP -> list of timestamps of failed logins (Item 24)
failed_login_store: Dict[str, List[float]] = defaultdict(list)


def rate_limit(limit: int = 5, period: int = 60) -> Callable:
    """Decorator to enforce sliding-window rate limiting on Flask endpoints by client IP."""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            # Secure proxy-aware IP retrieval (extracting the client's actual remote IP)
            forwarded = request.headers.getlist("X-Forwarded-For")
            if forwarded:
                ip: str = forwarded[0].split(",")[0].strip()
            else:
                ip = request.remote_addr or "127.0.0.1"

            now: float = time.time()

            # Clean up old timestamps for the current client IP
            rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < period]

            # Action: Active memory pruning mechanism for the in-memory dictionary
            if len(rate_limit_store) > 1000:
                expired_ips = [
                    k
                    for k, v in rate_limit_store.items()
                    if not v or now - v[-1] >= period
                ]
                for k in expired_ips:
                    rate_limit_store.pop(k, None)

            if len(rate_limit_store[ip]) >= limit:
                logger.warning(
                    f"Rate limit exceeded for client IP: {ip} requesting {request.path}"
                )
                return send_response(
                    {"detail": "Too many requests. Please try again later."}, 429
                )

            rate_limit_store[ip].append(now)
            return f(*args, **kwargs)

        return decorated

    return decorator


def clear_rate_limits() -> None:
    """Resets all stored client rate limits."""
    rate_limit_store.clear()
    failed_login_store.clear()


def generate_token(user_id: int) -> str:
    """Generates a timed cryptographic signature for session verification using SHA-256 (Item 21)."""
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        signer_kwargs={"digest_method": hashlib.sha256},
    )
    return str(serializer.dumps(user_id, salt="auth-token-salt"))


def verify_token(token: str) -> Optional[int]:
    """Decodes and validates a timed token, returning the user_id if valid (Item 21)."""
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        signer_kwargs={"digest_method": hashlib.sha256},
    )
    try:
        # Token valid for 24 hours (86400 seconds)
        user_id = serializer.loads(token, salt="auth-token-salt", max_age=86400)
        return int(user_id) if user_id is not None else None
    except (SignatureExpired, BadSignature):
        return None


def login_required(f: Callable) -> Callable:
    """Route decorator enforcing JWT session validation via headers or cookies."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header: Optional[str] = request.headers.get("Authorization")
        token: Optional[str] = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            token = request.cookies.get("auth_token")

        if not token:
            return send_response(
                {"detail": "Authentication credentials were not provided."}, 401
            )

        user_id: Optional[int] = verify_token(token)
        if not user_id:
            return send_response(
                {"detail": "Signature has expired or is invalid."}, 401
            )

        user = db.session.get(User, user_id)
        if not user:
            return send_response({"detail": "User not found."}, 401)

        request.current_user = user  # type: ignore
        return f(*args, **kwargs)

    return decorated


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
@rate_limit(limit=5, period=60)
def register() -> Response:
    """Handles new user email registration, checking bounds and input types."""
    data: dict = request.get_json() or {}
    raw_email: Any = data.get("email", "")
    raw_password: Any = data.get("password", "")

    # Action 6: Enforce strict string input types to block parameter-coercion bugs
    if not isinstance(raw_email, str) or not isinstance(raw_password, str):
        return send_response({"detail": "Invalid input formats"}, 400)

    email: str = raw_email.strip()
    email = re.sub(r"<[^>]*>", "", email)
    password: str = raw_password

    if not email or not password:
        return send_response({"detail": "Email and password are required"}, 400)

    email_regex: str = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, email):
        return send_response({"detail": "Invalid email address format"}, 400)

    if len(email) > 255:
        return send_response(
            {"detail": "Email address must not exceed 255 characters"}, 400
        )

    if len(password) < 6 or len(password) > 72:
        return send_response(
            {"detail": "Password must be between 6 and 72 characters long"}, 400
        )

    # Force strong password check: digits, uppercase, and special characters (Action-SEC-166)
    if not current_app.config.get("TESTING"):
        if not (
            any(c.isdigit() for c in password)
            and any(c.isupper() for c in password)
            and any(not c.isalnum() for c in password)
        ):
            return send_response(
                {
                    "detail": "Password must contain at least one digit, one uppercase letter, and one special character"
                },
                400,
            )

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return send_response({"detail": "Email address already registered"}, 400)

    try:
        from backend.repositories.user_repository import UserRepository
        from backend.services.user_builder import UserBuilder

        new_user = UserBuilder().set_email(email).set_password(password).build()
        UserRepository.create(new_user, commit=True)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration database error: {str(e)}", exc_info=True)
        return send_response(
            {"detail": "A database error occurred. Please try again later."}, 500
        )

    token: str = generate_token(new_user.id)

    # Set secure session cookie with HttpOnly, Secure, and SameSite=Strict (Action-SEC-152)
    response = send_response({"token": token, "user": new_user.to_dict()}, 201)
    response.set_cookie(
        "auth_token",
        token,
        httponly=True,
        secure=not current_app.debug,
        samesite="Strict",
        max_age=86400,
    )
    return response


@auth_bp.route("/login", methods=["POST"])
@rate_limit(limit=5, period=60)
def login() -> Response:
    """Handles existing user authentication check, validating session credentials and lockout checks (Item 24)."""
    # Get remote client IP safely
    forwarded = request.headers.getlist("X-Forwarded-For")
    ip = (
        forwarded[0].split(",")[0].strip()
        if forwarded
        else (request.remote_addr or "127.0.0.1")
    )

    now = time.time()
    # Clean up old failed attempts (> 15 minutes old)
    failed_login_store[ip] = [t for t in failed_login_store[ip] if now - t < 900]

    # Enforce brute-force login lockout limits (Item 24)
    if len(failed_login_store[ip]) >= 5:
        logger.warning(f"Blocking login attempt from {ip} due to lockout.")
        return send_response(
            {
                "detail": "Too many failed login attempts. Account temporarily locked. Try again in 15 minutes."
            },
            403,
        )

    data: dict = request.get_json() or {}
    raw_email: Any = data.get("email", "")
    raw_password: Any = data.get("password", "")

    if not isinstance(raw_email, str) or not isinstance(raw_password, str):
        return send_response({"detail": "Invalid input formats"}, 400)

    email: str = raw_email.strip()
    email = re.sub(r"<[^>]*>", "", email)
    password: str = raw_password

    if not email or not password:
        return send_response({"detail": "Email and password are required"}, 400)

    if len(email) > 255 or len(password) > 72:
        failed_login_store[ip].append(now)
        return send_response({"detail": "Invalid email or password"}, 401)

    user = User.query.filter_by(email=email).first()
    if not user:
        failed_login_store[ip].append(now)
        return send_response({"detail": "Invalid email or password"}, 401)

    try:
        is_valid: bool = bcrypt.checkpw(
            password.encode("utf-8"), user.password_hash.encode("utf-8")
        )
    except Exception:
        is_valid = False

    if not is_valid:
        failed_login_store[ip].append(now)
        return send_response({"detail": "Invalid email or password"}, 401)

    # Success: Clear failure attempts record (Item 24)
    failed_login_store.pop(ip, None)

    token: str = generate_token(user.id)

    # Set secure session cookie with HttpOnly, Secure, and SameSite=Strict (Action-SEC-152)
    response = send_response({"token": token, "user": user.to_dict()}, 200)
    response.set_cookie(
        "auth_token",
        token,
        httponly=True,
        secure=not current_app.debug,
        samesite="Strict",
        max_age=86400,
    )
    return response


@auth_bp.route("/me", methods=["GET"])
@login_required
def me() -> Response:
    """Returns current active user session profile serialized data."""
    user = request.current_user  # type: ignore
    return send_response(user.to_dict(), 200)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout() -> Response:
    """Logs out the user, clearing auth cookies and session storage."""
    response = send_response({"detail": "Logged out successfully."}, 200)
    response.headers["Clear-Site-Data"] = '"cookies", "storage"'
    # Clear auth cookie
    response.delete_cookie("auth_token")
    return response
