from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from sqlalchemy.sql import expression

from application.models.tenants import Tenant
from application.utils.time_ist import get_ist_now


class TenantRepository:

    @staticmethod
    def create_tenant(db: Session, tenant_data: dict) -> Tenant:
        tenant = Tenant(**tenant_data)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def get_tenant_by_id(db: Session, tenant_id: UUID) -> Tenant | None:
        stmt = select(Tenant).where(and_(Tenant.id == tenant_id, not Tenant.is_deleted))
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_tenant_by_short_code(db: Session, short_code: str) -> Tenant | None:
        stmt = select(Tenant).where(and_(Tenant.short_code == short_code, not Tenant.is_deleted))
        return db.execute(stmt).scalars().first()

    @staticmethod
    def check_short_code_exists(db: Session, short_code: str) -> bool:
        stmt = select(Tenant.id).where(expression.true() & Tenant.short_code == short_code)
        return db.execute(stmt).first() is not None

    @staticmethod
    def get_tenants_by_owner(db: Session, owner_user_id: UUID) -> list[Tenant]:
        stmt = select(Tenant).where(and_(Tenant.owner_user_id == owner_user_id, not Tenant.is_deleted))
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update_tenant(db: Session, tenant: Tenant, update_data: dict) -> Tenant:
        for key, value in update_data.items():
            setattr(tenant, key, value)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def soft_delete_tenant(db: Session, tenant: Tenant) -> Tenant:
        tenant.is_deleted = True
        tenant.deleted_at = get_ist_now()
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant
