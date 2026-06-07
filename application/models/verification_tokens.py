import enum
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Uuid
from application.db.session import Base
from application.utils.time_ist import get_ist_now


class TokenPurpose(str, enum.Enum):
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    FORGOT_PASSWORD = "FORGOT_PASSWORD"


class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    email_id = Column(String, nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hash of the token
    purpose = Column(Enum(TokenPurpose), nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_ist_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_ist_now, onupdate=get_ist_now, nullable=False)
