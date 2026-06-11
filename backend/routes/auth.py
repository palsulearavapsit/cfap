from flask import request, Blueprint, Response, current_app
from functools import wraps
from collections import defaultdict
import time
import re
import bcrypt
import logging
from typing import Callable, Any, Optional
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from backend.models import db, User
from backend.utils import send_response

logger = logging.getLogger("ecotrack.auth")

# In-memory rate limiter: IP -> list of timestamps of requests
rate_limit_store = defaultdict(list)

def rate_limit(limit: int = 5, period: int = 60) -> Callable:
    """Decorator to enforce sliding-window rate limiting on Flask endpoints by client IP.
    
    Includes memory cleanup logic and secure proxy-aware IP parsing.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            # Secure proxy-aware IP retrieval (extracting the client's actual remote IP)
            forwarded = request.headers.getlist("X-Forwarded-For")
            if forwarded:
                ip: str = forwarded[0].split(',')[0].strip()
            else:
                ip = request.remote_addr or '127.0.0.1'
                
            now: float = time.time()
            
            # Clean up old timestamps for the current client IP
            rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < period]
            
            # Action: Active memory pruning mechanism for the in-memory dictionary
            if len(rate_limit_store) > 1000:
                expired_ips = [k for k, v in rate_limit_store.items() if not v or now - v[-1] >= period]
                for k in expired_ips:
                    rate_limit_store.pop(k, None)
                    
            if len(rate_limit_store[ip]) >= limit:
                logger.warning(f"Rate limit exceeded for client IP: {ip} requesting {request.path}")
                return send_response({"detail": "Too many requests. Please try again later."}, 429)
                
            rate_limit_store[ip].append(now)
            return f(*args, **kwargs)
        return decorated
    return decorator

def clear_rate_limits() -> None:
    """Resets all stored client rate limits."""
    rate_limit_store.clear()

def generate_token(user_id: int) -> str:
    """Generates a timed cryptographic signature for session verification."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return str(serializer.dumps(user_id, salt='auth-token-salt'))

def verify_token(token: str) -> Optional[int]:
    """Decodes and validates a timed token, returning the user_id if valid."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        # Token valid for 24 hours (86400 seconds)
        user_id = serializer.loads(token, salt='auth-token-salt', max_age=86400)
        return int(user_id) if user_id is not None else None
    except (SignatureExpired, BadSignature):
        return None

def login_required(f: Callable) -> Callable:
    """Route decorator enforcing JWT session validation via headers or cookies."""
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header: Optional[str] = request.headers.get('Authorization')
        token: Optional[str] = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            token = request.cookies.get('auth_token')
            
        if not token:
            return send_response({"detail": "Authentication credentials were not provided."}, 401)
            
        user_id: Optional[int] = verify_token(token)
        if not user_id:
            return send_response({"detail": "Signature has expired or is invalid."}, 401)
            
        user = db.session.get(User, user_id)
        if not user:
            return send_response({"detail": "User not found."}, 401)
            
        request.current_user = user # type: ignore
        return f(*args, **kwargs)
    return decorated

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
@rate_limit(limit=5, period=60)
def register() -> Response:
    """Handles new user email registration, checking bounds and input types."""
    data: dict = request.get_json() or {}
    raw_email: Any = data.get('email', '')
    raw_password: Any = data.get('password', '')

    # Action 6: Enforce strict string input types to block parameter-coercion bugs
    if not isinstance(raw_email, str) or not isinstance(raw_password, str):
        return send_response({"detail": "Invalid input formats"}, 400)

    email: str = raw_email.strip()
    password: str = raw_password

    if not email or not password:
        return send_response({"detail": "Email and password are required"}, 400)

    email_regex: str = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return send_response({"detail": "Invalid email address format"}, 400)

    if len(email) > 255:
        return send_response({"detail": "Email address must not exceed 255 characters"}, 400)

    if len(password) < 6 or len(password) > 72:
        return send_response({"detail": "Password must be between 6 and 72 characters long"}, 400)

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return send_response({"detail": "Email address already registered"}, 400)

    salt: bytes = bcrypt.gensalt()
    hashed: str = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    try:
        new_user = User(email=email, password_hash=hashed)
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration database error: {str(e)}", exc_info=True)
        return send_response({"detail": "A database error occurred. Please try again later."}, 500)

    token: str = generate_token(new_user.id)
    # Action 3: Serialize user record output using the model's to_dict() method
    return send_response({
        "token": token,
        "user": new_user.to_dict()
    }, 201)

@auth_bp.route('/login', methods=['POST'])
@rate_limit(limit=5, period=60)
def login() -> Response:
    """Handles existing user authentication check, validating session credentials."""
    data: dict = request.get_json() or {}
    raw_email: Any = data.get('email', '')
    raw_password: Any = data.get('password', '')

    # Action 6: Enforce strict string input types to block parameter-coercion bugs
    if not isinstance(raw_email, str) or not isinstance(raw_password, str):
        return send_response({"detail": "Invalid input formats"}, 400)

    email: str = raw_email.strip()
    password: str = raw_password

    if not email or not password:
        return send_response({"detail": "Email and password are required"}, 400)

    if len(email) > 255 or len(password) > 72:
        return send_response({"detail": "Invalid email or password"}, 401)

    user = User.query.filter_by(email=email).first()
    if not user:
        return send_response({"detail": "Invalid email or password"}, 401)

    try:
        is_valid: bool = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
    except Exception:
        is_valid = False

    if not is_valid:
        return send_response({"detail": "Invalid email or password"}, 401)

    token: str = generate_token(user.id)
    # Action 3: Serialize user record output using the model's to_dict() method
    return send_response({
        "token": token,
        "user": user.to_dict()
    }, 200)

@auth_bp.route('/me', methods=['GET'])
@login_required
def me() -> Response:
    """Returns current active user session profile serialized data."""
    user = request.current_user # type: ignore
    # Action 3: Serialize user record output using the model's to_dict() method
    return send_response(user.to_dict(), 200)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout() -> Response:
    """Logs out the user, clearing auth cookies and session storage."""
    response = send_response({"detail": "Logged out successfully."}, 200)
    response.headers['Clear-Site-Data'] = '"cookies", "storage"'
    return response
