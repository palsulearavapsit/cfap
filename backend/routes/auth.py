from flask import request
from backend.models import db, User

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        # Automatically load or create a default user with ID 1 (no login required)
        default_user = User.query.get(1)
        if not default_user:
            default_user = User(id=1, email="user@ecotrack.ai", password_hash="disabled")
            db.session.add(default_user)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                default_user = User.query.filter_by(email="user@ecotrack.ai").first()
                if not default_user:
                    default_user = User(email="user@ecotrack.ai", password_hash="disabled")
                    db.session.add(default_user)
                    db.session.commit()
        
        request.current_user = default_user
        return f(*args, **kwargs)
    return decorated

