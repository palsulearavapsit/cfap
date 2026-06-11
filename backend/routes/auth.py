from flask import request, jsonify, current_app, Blueprint, Response
from functools import wraps
from collections import defaultdict
import time
import re
import bcrypt
from typing import Callable, Any, Optional
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from backend.models import db, User

# In-memory rate limiter: IP -> list of timestamps of requests
rate_limit_store = defaultdict(list)

def rate_limit(limit: int = 5, period: int = 60) -> Callable:
    """Decorator to enforce sliding-window rate limiting on Flask endpoints by client IP."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            ip: str = request.remote_addr or '127.0.0.1'
            now: float = time.time()
            # Clean up old timestamps
            rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < period]
            if len(rate_limit_store[ip]) >= limit:
                return jsonify({"detail": "Too many requests. Please try again later."}), 429
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
            return jsonify({"detail": "Authentication credentials were not provided."}), 401
            
        user_id: Optional[int] = verify_token(token)
        if not user_id:
            return jsonify({"detail": "Signature has expired or is invalid."}), 401
            
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"detail": "User not found."}), 401
            
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
        return jsonify({"detail": "Invalid input formats"}), 400

    email: str = raw_email.strip()
    password: str = raw_password

    if not email or not password:
        return jsonify({"detail": "Email and password are required"}), 400

    email_regex: str = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return jsonify({"detail": "Invalid email address format"}), 400

    if len(email) > 255:
        return jsonify({"detail": "Email address must not exceed 255 characters"}), 400

    if len(password) < 6 or len(password) > 72:
        return jsonify({"detail": "Password must be between 6 and 72 characters long"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"detail": "Email address already registered"}), 400

    salt: bytes = bcrypt.gensalt()
    hashed: str = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    try:
        new_user = User(email=email, password_hash=hashed)
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"detail": f"Database error: {str(e)}"}), 500

    token: str = generate_token(new_user.id)
    # Action 3: Serialize user record output using the model's to_dict() method
    return jsonify({
        "token": token,
        "user": new_user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
@rate_limit(limit=5, period=60)
def login() -> Response:
    """Handles existing user authentication check, validating session credentials."""
    data: dict = request.get_json() or {}
    raw_email: Any = data.get('email', '')
    raw_password: Any = data.get('password', '')

    # Action 6: Enforce strict string input types to block parameter-coercion bugs
    if not isinstance(raw_email, str) or not isinstance(raw_password, str):
        return jsonify({"detail": "Invalid input formats"}), 400

    email: str = raw_email.strip()
    password: str = raw_password

    if not email or not password:
        return jsonify({"detail": "Email and password are required"}), 400

    if len(password) > 72:
        return jsonify({"detail": "Invalid email or password"}), 401

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"detail": "Invalid email or password"}), 401

    try:
        is_valid: bool = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
    except Exception:
        is_valid = False

    if not is_valid:
        return jsonify({"detail": "Invalid email or password"}), 401

    token: str = generate_token(user.id)
    # Action 3: Serialize user record output using the model's to_dict() method
    return jsonify({
        "token": token,
        "user": user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def me() -> Response:
    """Returns current active user session profile serialized data."""
    user = request.current_user # type: ignore
    # Action 3: Serialize user record output using the model's to_dict() method
    return jsonify(user.to_dict()), 200
