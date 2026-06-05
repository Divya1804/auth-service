import bcrypt
import jwt
from datetime import timedelta
from application.core.config import settings
from application.utils.time_ist import get_ist_now


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: dict, expires_delta: timedelta | None = None) -> str:
    """Create a new access token (JWT) with IST expiration."""
    expire = get_ist_now() + expires_delta if expires_delta else get_ist_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY_TIME)

    to_encode = {"exp": expire, "sub": str(subject.get("user_id")), "user": subject.copy()}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
