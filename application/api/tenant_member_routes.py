from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.orm import Session

from application.db.dependencies import get_db
from application.schemas.tenant_invites import TenantInviteCreate, AcceptInviteRequest
from application.schemas.tenant_members import UpdateMemberRolesRequest
from application.services.tenant_member_service import TenantMemberService
from application.utils.response import success_response
from application.models.users import User
from application.models.tenant_members import TenantMember
from application.core.authz import RequireAuth, RequireTenant, RequirePermissions, RequireRoles

router = APIRouter(prefix="/tenants", tags=["Tenant Members & Invites"])


@router.post("/{tenant_id}/invitations")
def invite_member(
    tenant_id: UUID,
    request_data: TenantInviteCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireAuth()),
    tenant_member: TenantMember = Depends(RequireRoles(["Owner", "Admin"])),
):
    base_url = str(request.base_url).rstrip("/")
    invite = TenantMemberService.invite_member(db, tenant_member.tenant_id, current_user.user_id, request_data, background_tasks, base_url)
    return success_response(201, "Invitation sent successfully", data=invite.model_dump())


@router.post("/invitations/accept")
def accept_invite(request_data: AcceptInviteRequest, db: Session = Depends(get_db)):
    result = TenantMemberService.accept_invite(db, request_data)
    return success_response(200, result["message"])


@router.get("/{tenant_id}/members")
def get_tenant_members(tenant_id: UUID, db: Session = Depends(get_db), tenant_member: TenantMember = Depends(RequirePermissions(["read"]))):
    members = TenantMemberService.get_tenant_members(db, tenant_member.tenant_id)
    return success_response(200, "Members fetched successfully", data=[m.model_dump() for m in members])


@router.get("/{tenant_id}/invitations")
def get_tenant_invites(tenant_id: UUID, db: Session = Depends(get_db), tenant_member: TenantMember = Depends(RequireRoles(["Owner", "Admin"]))):
    invites = TenantMemberService.get_tenant_invites(db, tenant_member.tenant_id)
    return success_response(200, "Invitations fetched successfully", data=[i.model_dump() for i in invites])


@router.patch("/{tenant_id}/members/{user_id}/roles")
def update_member_roles(tenant_id: UUID, user_id: UUID, request_data: UpdateMemberRolesRequest, db: Session = Depends(get_db), tenant_member: TenantMember = Depends(RequireRoles(["Owner", "Admin"]))):
    result = TenantMemberService.update_member_roles(db, tenant_member.tenant_id, user_id, request_data.role_ids)
    return success_response(200, "Roles updated successfully", data=result.model_dump())


@router.delete("/{tenant_id}/members/{user_id}")
def remove_member(tenant_id: UUID, user_id: UUID, db: Session = Depends(get_db), tenant_member: TenantMember = Depends(RequireRoles(["Owner", "Admin"]))):
    result = TenantMemberService.remove_member(db, tenant_member.tenant_id, user_id)
    return success_response(200, result["message"])


@router.delete("/{tenant_id}/invitations/{invite_id}")
def cancel_invite(tenant_id: UUID, invite_id: UUID, db: Session = Depends(get_db), tenant_member: TenantMember = Depends(RequireRoles(["Owner", "Admin"]))):
    result = TenantMemberService.cancel_invite(db, tenant_member.tenant_id, invite_id)
    return success_response(200, result["message"])


@router.post("/{tenant_id}/leave")
def leave_tenant(tenant_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(RequireAuth()), tenant_member: TenantMember = Depends(RequireTenant())):
    result = TenantMemberService.leave_tenant(db, tenant_member.tenant_id, current_user.user_id)
    return success_response(200, result["message"])
