from typing import Optional

from backend.models import User, db


class UserRepository:
    """Repository class for User database operations."""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        return User.query.filter_by(email=email).first()

    @staticmethod
    def create(user: User, commit: bool = True) -> User:
        db.session.add(user)
        if commit:
            db.session.commit()
        return user
