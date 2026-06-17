from typing import Optional
import bcrypt
from flask import current_app
from backend.models import User

class UserBuilder:
    """Builder class to standardise User model creation logic."""

    def __init__(self) -> None:
        self._email: Optional[str] = None
        self._password: Optional[str] = None

    def set_email(self, email: str) -> "UserBuilder":
        self._email = email
        return self

    def set_password(self, password: str) -> "UserBuilder":
        self._password = password
        return self

    def build(self) -> User:
        if not self._email:
            raise ValueError("Email is required to build a User")
        if not self._password:
            raise ValueError("Password is required to build a User")

        # Hash password using configured bcrypt rounds
        rounds = current_app.config.get("BCRYPT_LOG_ROUNDS", 12)
        salt: bytes = bcrypt.gensalt(rounds=rounds)
        hashed: str = bcrypt.hashpw(self._password.encode("utf-8"), salt).decode("utf-8")

        return User(email=self._email, password_hash=hashed)
