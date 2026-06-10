from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from application.models.tenant_members import TenantMemberStatus


class TenantMemberResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    role_ids: list[UUID]
    status: TenantMemberStatus
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
