import random
import string
from uuid import UUID
from sqlalchemy.orm import Session

from application.repositories.tenant_repo import TenantRepository
from application.repositories.user_repo import UserRepository
from application.repositories.role_repo import RoleRepository
from application.repositories.tenant_member_repo import TenantMemberRepository
from application.models.tenant_members import TenantMemberStatus
from application.schemas.tenants import TenantCreate, TenantUpdate, TenantResponse
from application.core.exceptions import BadRequestException
from application.utils.logger import auth_logger


class TenantService:

    @staticmethod
    def _generate_unique_short_code(db: Session, name: str) -> str:
        # Create a base code from the name: alphanumeric only, upper case, max 6 chars
        base = "".join(e for e in name if e.isalnum()).upper()[:6]
        if not base:
            base = "TEN"

        # Try base first
        if not TenantRepository.check_short_code_exists(db, base):
            return base

        # If collision, append random strings until unique
        while True:
            random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            short_code = f"{base}_{random_suffix}"
            if not TenantRepository.check_short_code_exists(db, short_code):
                return short_code

    @staticmethod
    def create_tenant(db: Session, user_id: UUID, request: TenantCreate) -> TenantResponse:
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            raise BadRequestException("User not found")

        short_code = TenantService._generate_unique_short_code(db, request.name)

        tenant_data = request.model_dump()
        tenant_data["short_code"] = short_code
        tenant_data["owner_user_id"] = user_id

        # Create tenant
        tenant = TenantRepository.create_tenant(db, tenant_data)

        # Assign Owner Role to Creator
        owner_role = RoleRepository.get_role_by_name(db, "Owner")
        if owner_role:
            TenantMemberRepository.create_member(db=db, tenant_id=tenant.id, user_id=user_id, role_ids=[owner_role.id], status=TenantMemberStatus.ACTIVE)

        # Update User
        # JSON type returns a list, but assigning requires creating a new list object for SQLAlchemy to detect change
        updated_tenant_lists = list(user.tenant_lists) if user.tenant_lists else []
        updated_tenant_lists.append(str(tenant.id))

        update_data = {"tenant_lists": updated_tenant_lists}
        if user.default_tenant is None:
            update_data["default_tenant"] = tenant.id

        UserRepository.update_user(db, user, update_data)

        auth_logger.info(f"Tenant {short_code} created successfully by user {user_id} with Owner role.")
        return TenantResponse.model_validate(tenant)

    @staticmethod
    def get_my_tenants(db: Session, user_id: UUID) -> list[TenantResponse]:
        # Using the owner_user_id (could also use tenant_lists for assigned tenants)
        tenants = TenantRepository.get_tenants_by_owner(db, user_id)
        return [TenantResponse.model_validate(t) for t in tenants]

    @staticmethod
    def get_tenant(db: Session, user_id: UUID, tenant_id: UUID) -> TenantResponse:
        tenant = TenantRepository.get_tenant_by_id(db, tenant_id)
        if not tenant:
            raise BadRequestException("Tenant not found")

        # Basic ownership check
        if tenant.owner_user_id != user_id:
            raise BadRequestException("Unauthorized access to tenant")

        return TenantResponse.model_validate(tenant)

    @staticmethod
    def update_tenant(db: Session, user_id: UUID, tenant_id: UUID, request: TenantUpdate) -> TenantResponse:
        tenant = TenantRepository.get_tenant_by_id(db, tenant_id)
        if not tenant:
            raise BadRequestException("Tenant not found")

        if tenant.owner_user_id != user_id:
            raise BadRequestException("Unauthorized access to tenant")

        update_data = request.model_dump(exclude_unset=True)
        updated_tenant = TenantRepository.update_tenant(db, tenant, update_data)

        return TenantResponse.model_validate(updated_tenant)

    @staticmethod
    def delete_tenant(db: Session, user_id: UUID, tenant_id: UUID) -> dict:
        tenant = TenantRepository.get_tenant_by_id(db, tenant_id)
        if not tenant:
            raise BadRequestException("Tenant not found")

        if tenant.owner_user_id != user_id:
            raise BadRequestException("Unauthorized access to tenant")

        TenantRepository.soft_delete_tenant(db, tenant)
        auth_logger.info(f"Tenant {tenant_id} soft deleted by user {user_id}")

        user = UserRepository.get_user_by_id(db, user_id)
        if user:
            update_data = {}
            if user.default_tenant == tenant_id:
                # If they have other tenants, make the first one default, else None
                remaining = [t for t in user.tenant_lists if t != str(tenant_id)]
                update_data["default_tenant"] = UUID(remaining[0]) if remaining else None

            if str(tenant_id) in user.tenant_lists:
                updated_list = [t for t in user.tenant_lists if t != str(tenant_id)]
                update_data["tenant_lists"] = updated_list

            if update_data:
                UserRepository.update_user(db, user, update_data)

        return {"message": "Tenant deleted successfully"}
