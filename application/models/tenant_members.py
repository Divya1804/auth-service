import enum
import uuid
from sqlalchemy import Column, JSON, DateTime, ForeignKey, Enum, Uuid
from application.db.session import Base
from application.utils.time_ist import get_ist_now


class TenantMemberStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"


class TenantMember(Base):
    __tablename__ = "tenant_members"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)

    role_ids = Column(JSON, default=list, nullable=False)

    status = Column(Enum(TenantMemberStatus), default=TenantMemberStatus.PENDING, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=get_ist_now, nullable=False)
