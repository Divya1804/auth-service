from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from sqlalchemy.sql import expression

from application.models.tenant_members import TenantMember, TenantMemberStatus


class TenantMemberRepository:
    @staticmethod
    def get_members_by_tenant(db: Session, tenant_id: UUID) -> list[TenantMember]:
        stmt = select(TenantMember).where(expression.true() & TenantMember.tenant_id == tenant_id)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_member(db: Session, tenant_id: UUID, user_id: UUID) -> TenantMember | None:
        stmt = select(TenantMember).where(and_(TenantMember.tenant_id == tenant_id, TenantMember.user_id == user_id))
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create_member(db: Session, tenant_id: UUID, user_id: UUID, role_ids: list[UUID], status: TenantMemberStatus = TenantMemberStatus.ACTIVE) -> TenantMember:
        # Check if exists to prevent duplicates
        existing = TenantMemberRepository.get_member(db, tenant_id, user_id)
        if existing:
            return existing

        member = TenantMember(tenant_id=tenant_id, user_id=user_id, role_ids=[str(r) for r in role_ids], status=status)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def update_member_status(db: Session, member_id: UUID, status: TenantMemberStatus) -> TenantMember | None:
        stmt = select(TenantMember).where(expression.true() & TenantMember.id == member_id)
        member = db.execute(stmt).scalars().first()
        if member:
            member.status = status
            db.commit()
            db.refresh(member)
        return member

    @staticmethod
    def update_member_roles(db: Session, member: TenantMember, role_ids: list[UUID]) -> TenantMember:
        member.role_ids = [str(r) for r in role_ids]
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove_member(db: Session, tenant_id: UUID, user_id: UUID) -> bool:
        member = TenantMemberRepository.get_member(db, tenant_id, user_id)
        if member:
            db.delete(member)
            db.commit()
            return True
        return False
