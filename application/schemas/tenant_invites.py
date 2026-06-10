from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from application.models.tenant_invites import InviteStatus


class TenantInviteCreate(BaseModel):
    email_id: EmailStr
    role_ids: list[UUID]


class TenantInviteResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email_id: str
    invited_by: UUID
    role_ids: list[UUID]
    status: InviteStatus
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AcceptInviteRequest(BaseModel):
    token: str
