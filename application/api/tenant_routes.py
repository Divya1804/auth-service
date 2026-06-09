from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.db.dependencies import get_db
from application.schemas.tenants import TenantCreate, TenantUpdate
from application.services.tenant_service import TenantService
from application.utils.response import success_response
from application.api.dependencies import get_current_user, get_current_tenant
from application.models.users import User

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("/")
def create_tenant(request: TenantCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant = TenantService.create_tenant(db, current_user.user_id, request)
    return success_response(201, "Tenant created successfully", data=tenant.model_dump())


@router.get("/")
def get_my_tenants(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenants = TenantService.get_my_tenants(db, current_user.user_id)
    return success_response(200, "Tenants fetched successfully", data=[t.model_dump() for t in tenants])


@router.get("/{tenant_id}")
def get_tenant(tenant_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant = TenantService.get_tenant(db, current_user.user_id, tenant_id)
    return success_response(200, "Tenant details fetched successfully", data=tenant.model_dump())


@router.patch("/{tenant_id}")
def update_tenant(tenant_id: UUID, request: TenantUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant = TenantService.update_tenant(db, current_user.user_id, tenant_id, request)
    return success_response(200, "Tenant updated successfully", data=tenant.model_dump())


@router.delete("/{tenant_id}")
def delete_tenant(tenant_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    TenantService.delete_tenant(db, current_user.user_id, tenant_id)
    return success_response(200, "Tenant deleted successfully")


# Example endpoint demonstrating X-Tenant-Id dependency usage
@router.get("/context/demo")
def context_demo(
    active_tenant_id: UUID = Depends(get_current_tenant),
):
    return success_response(200, "Context active", data={"active_tenant_id": str(active_tenant_id)})
