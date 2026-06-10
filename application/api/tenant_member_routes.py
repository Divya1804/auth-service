from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.orm import Session

from application.db.dependencies import get_db
from application.schemas.tenant_invites import TenantInviteCreate, AcceptInviteRequest
from application.services.tenant_member_service import TenantMemberService
from application.utils.response import success_response
from application.api.dependencies import get_current_user
from application.models.users import User

router = APIRouter(prefix="/tenants", tags=["Tenant Members & Invites"])


@router.post("/{tenant_id}/invitations")
def invite_member(
    tenant_id: UUID, request_data: TenantInviteCreate, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # In a full RBAC system, we would check if current_user is Admin/Owner for this tenant here.
    base_url = str(request.base_url).rstrip("/")
    invite = TenantMemberService.invite_member(db, tenant_id, current_user.user_id, request_data, background_tasks, base_url)
    return success_response(201, "Invitation sent successfully", data=invite.model_dump())


@router.post("/invitations/accept")
def accept_invite(request_data: AcceptInviteRequest, db: Session = Depends(get_db)):
    # This endpoint doesn't require get_current_user because the user is accepting an invite
    # via a token from email. The service layer verifies the token and user existence.
    result = TenantMemberService.accept_invite(db, request_data)
    return success_response(200, result["message"])


@router.get("/{tenant_id}/members")
def get_tenant_members(tenant_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # In a full RBAC system, we would check if current_user has read access.
    members = TenantMemberService.get_tenant_members(db, tenant_id)
    return success_response(200, "Members fetched successfully", data=[m.model_dump() for m in members])


@router.get("/{tenant_id}/invitations")
def get_tenant_invites(tenant_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # In a full RBAC system, we would check if current_user has read access.
    invites = TenantMemberService.get_tenant_invites(db, tenant_id)
    return success_response(200, "Invitations fetched successfully", data=[i.model_dump() for i in invites])
