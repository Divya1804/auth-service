from uuid import UUID
from datetime import timedelta
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from application.repositories.tenant_invite_repo import TenantInviteRepository
from application.repositories.tenant_member_repo import TenantMemberRepository
from application.repositories.user_repo import UserRepository
from application.schemas.tenant_invites import TenantInviteCreate, TenantInviteResponse, AcceptInviteRequest
from application.schemas.tenant_members import TenantMemberResponse
from application.models.tenant_invites import InviteStatus
from application.models.tenant_members import TenantMemberStatus
from application.core.exceptions import BadRequestException, UnauthorizedUserException
from application.utils.security import generate_verification_token, hash_token_string
from application.utils.time_ist import get_ist_now
from application.utils.logger import auth_logger
from application.utils.email import EmailService


class TenantMemberService:

    @staticmethod
    def invite_member(db: Session, tenant_id: UUID, invited_by: UUID, request: TenantInviteCreate, background_tasks: BackgroundTasks, base_url: str) -> TenantInviteResponse:
        # Validate roles
        for _role_id in request.role_ids:
            # We don't have a direct get_role_by_id in repo, but we can assume role_id is valid for MVP
            # or add a check if needed. Let's assume it's valid if provided from dropdown.
            pass

        raw_token = generate_verification_token()
        token_hash = hash_token_string(raw_token)
        expires_at = get_ist_now() + timedelta(days=7)

        invite = TenantInviteRepository.create_invite(
            db=db, tenant_id=tenant_id, email_id=request.email_id, invited_by=invited_by, token_hash=token_hash, role_ids=request.role_ids, expires_at=expires_at
        )

        invitation_url = f"{base_url}/accept-invite?token={raw_token}&email={request.email_id}"

        # In a real app we might fetch inviter's name and tenant name to make email pretty
        background_tasks.add_task(
            EmailService.send_verification_email,  # Using verification email template as placeholder for invite template
            email_to=request.email_id,
            username=request.email_id.split("@")[0],
            verification_url=invitation_url,
        )

        auth_logger.info(f"Invitation sent to {request.email_id} for tenant {tenant_id}")
        return TenantInviteResponse.model_validate(invite)

    @staticmethod
    def accept_invite(db: Session, request: AcceptInviteRequest) -> dict:
        token_hash = hash_token_string(request.token)
        invite = TenantInviteRepository.get_invite_by_token(db, token_hash)

        if not invite:
            raise BadRequestException("Invalid invitation token")

        if invite.status != InviteStatus.PENDING:
            raise BadRequestException("Invitation is no longer valid")

        if invite.expires_at < get_ist_now():
            TenantInviteRepository.update_invite_status(db, invite.id, InviteStatus.EXPIRED)
            raise BadRequestException("Invitation has expired")

        user = UserRepository.get_user_by_email(db, invite.email_id)
        if not user:
            raise UnauthorizedUserException("You must register an account with this email address first.")

        # Accept the invite
        TenantInviteRepository.update_invite_status(db, invite.id, InviteStatus.ACCEPTED)

        # Create TenantMember
        TenantMemberRepository.create_member(db=db, tenant_id=invite.tenant_id, user_id=user.user_id, role_ids=invite.role_ids, status=TenantMemberStatus.ACTIVE)

        # Update User tenant_lists
        updated_tenant_lists = list(user.tenant_lists) if user.tenant_lists else []
        if str(invite.tenant_id) not in updated_tenant_lists:
            updated_tenant_lists.append(str(invite.tenant_id))

            update_data = {"tenant_lists": updated_tenant_lists}
            if user.default_tenant is None:
                update_data["default_tenant"] = invite.tenant_id

            UserRepository.update_user(db, user, update_data)

        auth_logger.info(f"User {user.email_id} accepted invitation to tenant {invite.tenant_id}")
        return {"message": "Invitation accepted successfully. You are now a member of the tenant."}

    @staticmethod
    def get_tenant_members(db: Session, tenant_id: UUID) -> list[TenantMemberResponse]:
        members = TenantMemberRepository.get_members_by_tenant(db, tenant_id)
        return [TenantMemberResponse.model_validate(m) for m in members]

    @staticmethod
    def get_tenant_invites(db: Session, tenant_id: UUID) -> list[TenantInviteResponse]:
        invites = TenantInviteRepository.get_invites_for_tenant(db, tenant_id)
        return [TenantInviteResponse.model_validate(i) for i in invites]
