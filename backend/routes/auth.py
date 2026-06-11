from flask import request, jsonify, current_app, Blueprint
from functools import wraps
from collections import defaultdict
import time
import re
import bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from backend.models import db, User

# In-memory rate limiter: IP -> list of timestamps of requests
rate_limit_store = defaultdict(list)

def rate_limit(limit=5, period=60):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            ip = request.remote_addr
            now = time.time()
            # Clean up old timestamps
            rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < period]
            if len(rate_limit_store[ip]) >= limit:
                return jsonify({"detail": "Too many requests. Please try again later."}), 429
            rate_limit_store[ip].append(now)
            return f(*args, **kwargs)
        return decorated
    return decorator

def clear_rate_limits():
    rate_limit_store.clear()

def generate_token(user_id):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(user_id, salt='auth-token-salt')

def verify_token(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        # Token valid for 24 hours (86400 seconds)
        user_id = serializer.loads(token, salt='auth-token-salt', max_age=86400)
        return user_id
    except (SignatureExpired, BadSignature):
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            token = request.cookies.get('auth_token')
            
        if not token:
            return jsonify({"detail": "Authentication credentials were not provided."}), 401
            
        user_id = verify_token(token)
        if not user_id:
            return jsonify({"detail": "Signature has expired or is invalid."}), 401
            
        # Avoid Query.get() legacy warning by using db.session.get(User, user_id)
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"detail": "User not found."}), 401
            
        request.current_user = user
        return f(*args, **kwargs)
    return decorated

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
@rate_limit(limit=5, period=60)
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"detail": "Email and password are required"}), 400

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return jsonify({"detail": "Invalid email address format"}), 400

    if len(password) < 6:
        return jsonify({"detail": "Password must be at least 6 characters long"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"detail": "Email address already registered"}), 400

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    try:
        new_user = User(email=email, password_hash=hashed)
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"detail": f"Database error: {str(e)}"}), 500

    token = generate_token(new_user.id)
    return jsonify({
        "token": token,
        "user": {
            "id": new_user.id,
            "email": new_user.email
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
@rate_limit(limit=5, period=60)
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"detail": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"detail": "Invalid email or password"}), 401

    try:
        is_valid = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
    except Exception:
        is_valid = False

    if not is_valid:
        return jsonify({"detail": "Invalid email or password"}), 401

    token = generate_token(user.id)
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    user = request.current_user
    return jsonify({
        "id": user.id,
        "email": user.email
    }), 200
