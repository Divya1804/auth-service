import enum
import uuid
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Enum, Uuid
from application.db.session import Base
from application.utils.time_ist import get_ist_now


class InviteStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"


class TenantInvite(Base):
    __tablename__ = "tenant_invites"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email_id = Column(String, nullable=False, index=True)
    invited_by = Column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    token = Column(String, nullable=False, unique=True, index=True)
    role_ids = Column(JSON, default=list, nullable=False)

    status = Column(Enum(InviteStatus), default=InviteStatus.PENDING, nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=get_ist_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_ist_now, onupdate=get_ist_now, nullable=False)
