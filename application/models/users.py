import enum
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON, Uuid
from application.db.session import Base
from application.utils.time_ist import get_ist_now


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class User(Base):
    """
    # user_id: UUID, first_name, last_name, email_id, phone_no, username, password, address, city, state, pincode, img_url,
    # status [ACTIVE / INACTIVE],is_verified [T/F], last_login_at, created_at, updated_at, tenant_lists, default_tenant
    # status is active only after successful email verification.. -> is_verified = True then only status = ACTIVE
    # last_login_at needs to update everytime while hitting /login, /signup, /logout... (Need to Research)
    # tenant_list = list of tenant user have access for..
    # default_tenant = the tenant which user gets on the login default. without selecting.
    """

    __tablename__ = "users"

    user_id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    email_id = Column(String, nullable=False, unique=True, index=True)
    phone_no = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)

    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)

    img_url = Column(String, nullable=True)

    status = Column(Enum(UserStatus), default=UserStatus.INACTIVE, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_ist_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_ist_now, onupdate=get_ist_now, nullable=False)

    tenant_lists = Column(JSON, default=list, nullable=False)
    default_tenant = Column(Uuid(as_uuid=True), nullable=True)
