from uuid import UUID
from datetime import datetime

from pydantic import EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql import expression

from application.models.tenant_invites import TenantInvite, InviteStatus
from application.utils.time_ist import get_ist_now


class TenantInviteRepository:
    @staticmethod
    def create_invite(db: Session, tenant_id: UUID, email_id: EmailStr, invited_by: UUID, token_hash: str, role_ids: list[UUID], expires_at: datetime) -> TenantInvite:
        invite = TenantInvite(tenant_id=tenant_id, email_id=email_id, invited_by=invited_by, token=token_hash, role_ids=[str(r) for r in role_ids], expires_at=expires_at, status=InviteStatus.PENDING)
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return invite

    @staticmethod
    def get_invite_by_token(db: Session, token_hash: str) -> TenantInvite | None:
        stmt = select(TenantInvite).where(expression.true() & TenantInvite.token == token_hash)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_invites_for_tenant(db: Session, tenant_id: UUID) -> list[TenantInvite]:
        stmt = select(TenantInvite).where(expression.true() & TenantInvite.tenant_id == tenant_id)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update_invite_status(db: Session, invite_id: UUID, status: InviteStatus) -> TenantInvite | None:
        stmt = select(TenantInvite).where(expression.true() & TenantInvite.id == invite_id)
        invite = db.execute(stmt).scalars().first()
        if invite:
            invite.status = status
            if status == InviteStatus.ACCEPTED:
                invite.accepted_at = get_ist_now()
            db.commit()
            db.refresh(invite)
        return invite
