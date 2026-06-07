import bcrypt
import hashlib
import jwt
import secrets
from datetime import timedelta
import uuid
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
    now = get_ist_now()
    expire = now + expires_delta if expires_delta else now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY_TIME)

    to_encode = {"iat": now, "exp": expire, "sub": str(subject.get("user_id")), "type": "access", "user": subject.copy()}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: uuid.UUID, token_id: uuid.UUID, tenant_id: uuid.UUID | None = None, expires_delta: timedelta | None = None) -> str:
    """Create a new refresh token (JWT) with IST expiration."""
    now = get_ist_now()
    expire = now + expires_delta if expires_delta else now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"iat": now, "exp": expire, "sub": str(user_id), "jti": str(token_id), "type": "refresh"}
    if tenant_id:
        to_encode["tenant_id"] = str(tenant_id)

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def hash_token_string(token: str) -> str:
    """Compute SHA-256 hash of a token string for secure DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_verification_token() -> str:
    """Generate a secure, URL-safe random string for token verification."""
    return secrets.token_urlsafe(32)
