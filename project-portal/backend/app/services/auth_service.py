"""Authentication service."""
from datetime import timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.models.user import User, UserStatus


def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    """Verify username or email and password. Returns User if valid, None otherwise."""
    clean_id = identifier.strip().lower()
    # Try username first (case-insensitive), then email (case-insensitive)
    user = db.query(User).filter(func.lower(User.username) == clean_id).first()
    if not user:
        user = db.query(User).filter(func.lower(User.email) == clean_id).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_token_for_user(user: User) -> str:
    """Create a JWT access token for the given user."""
    data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
    }
    expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return create_access_token(data=data, expires_delta=expires)


def build_user_domain_display(user: User) -> Optional[str]:
    """Return the domain display name for a user, or None if ADMIN."""
    if user.domain is None:
        return None
    domain_map = {
        "AI": "AI",
        "CYBERSECURITY": "Cybersecurity",
        "OPEN_INNOVATION": "Open Innovation",
    }
    return domain_map.get(user.domain.name, user.domain.name)
