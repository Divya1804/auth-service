import enum
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Uuid
from application.db.session import Base
from application.utils.time_ist import get_ist_now


class TenantStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    short_code = Column(String, nullable=False, unique=True, index=True)

    owner_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)

    email_id = Column(String, nullable=False)
    phone_no = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    gst_no = Column(String, nullable=True)

    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)

    status = Column(Enum(TenantStatus), default=TenantStatus.ACTIVE, nullable=False)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_ist_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_ist_now, onupdate=get_ist_now, nullable=False)
