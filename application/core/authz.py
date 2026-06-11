from uuid import UUID
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql import expression

from application.core.exceptions import ForbiddenException
from application.db.dependencies import get_db
from application.api.dependencies import get_current_user, get_current_tenant
from application.models.users import User
from application.models.tenant_members import TenantMember, TenantMemberStatus
from application.models.roles import Role


# 1. RequireAuth
# We can just alias the existing `get_current_user`, but creating a class allows identical patterns
class RequireAuth:
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        return current_user


# 2. RequireTenant
class RequireTenant:
    def __call__(self, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), active_tenant_id: UUID = Depends(get_current_tenant)) -> TenantMember:

        # We need the specific TenantMember context to know their roles in THIS tenant
        stmt = select(TenantMember).where(
            expression.true() & TenantMember.tenant_id == active_tenant_id,
            expression.true() & TenantMember.user_id == current_user.user_id,
            expression.true() & TenantMember.status == TenantMemberStatus.ACTIVE,
        )
        tenant_member = db.execute(stmt).scalars().first()

        if not tenant_member:
            raise ForbiddenException("You are not an active member of this tenant.")

        # Attach to request state for easy access downstream
        request.state.tenant_member = tenant_member
        return tenant_member


# Helper to fetch roles from a member
def _get_roles_for_member(db: Session, member: TenantMember) -> list[Role]:
    if not member.role_ids:
        return []

    stmt = select(Role).where(Role.id.in_([UUID(r) for r in member.role_ids]))
    return list(db.execute(stmt).scalars().all())


# 3. RequirePermissions
class RequirePermissions:
    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions

    def __call__(self, request: Request, db: Session = Depends(get_db), tenant_member: TenantMember = Depends(RequireTenant())):

        roles = _get_roles_for_member(db, tenant_member)

        # Flatten all permissions from all roles the user has in this tenant
        user_permissions = set()
        for r in roles:
            user_permissions.update(r.permissions)

        # If user has master 'full_access', grant immediately
        if "full_access" in user_permissions:
            return tenant_member

        # Check if user has ALL required permissions
        for perm in self.required_permissions:
            if perm not in user_permissions:
                raise ForbiddenException(f"Missing required permission: {perm}")

        return tenant_member


# 4. RequireRoles
class RequireRoles:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, request: Request, db: Session = Depends(get_db), tenant_member: TenantMember = Depends(RequireTenant())):

        roles = _get_roles_for_member(db, tenant_member)
        user_role_names = [r.name for r in roles]

        # Check if user has ANY of the allowed roles
        has_role = any(role in user_role_names for role in self.allowed_roles)

        if not has_role:
            raise ForbiddenException(f"This action requires one of the following roles: {', '.join(self.allowed_roles)}")

        return tenant_member
