from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict

from application.models.tenants import TenantStatus


class TenantBase(BaseModel):
    name: str
    email_id: EmailStr
    phone_no: str
    address: str
    city: str
    state: str
    pincode: str
    image_url: str | None = None
    gst_no: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: str | None = None
    email_id: EmailStr | None = None
    phone_no: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    image_url: str | None = None
    gst_no: str | None = None
    status: TenantStatus | None = None


class TenantResponse(TenantBase):
    id: UUID
    short_code: str
    owner_user_id: UUID
    status: TenantStatus
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = None
