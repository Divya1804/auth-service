from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from application.db.dependencies import get_db
from application.schemas.users import UserCreate, UserLogin, UserUpdate, UserBase, TokenRefreshRequest
from application.services.user_service import UserService
from application.utils.response import success_response
from application.api.dependencies import get_current_user
from application.models.users import User

router = APIRouter(prefix="/users")


@router.post("/signup")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_name = request.headers.get("x-device-name")

    result = UserService.register_user(db, user_in, device_name=device_name, ip_address=ip_address, user_agent=user_agent)
    return success_response(201, "User registered successfully", data=result)


@router.post("/login")
def login(request: Request, user_login: UserLogin, db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_name = request.headers.get("x-device-name")

    result = UserService.authenticate_user(db, user_login, device_name=device_name, ip_address=ip_address, user_agent=user_agent)
    return success_response(200, "Login successful", data=result)


@router.post("/refresh")
def refresh_token(request: Request, body: TokenRefreshRequest, db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_name = request.headers.get("x-device-name")

    result = UserService.rotate_refresh_token(
        db,
        refresh_token_str=body.refresh_token,
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return success_response(200, "Token refreshed successfully", data=result)


@router.post("/logout")
def logout(body: TokenRefreshRequest, db: Session = Depends(get_db)):
    UserService.revoke_refresh_token(db, refresh_token_str=body.refresh_token)
    return success_response(200, "Logout successful")


@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    safe_profile = UserBase.model_validate(current_user)
    return success_response(200, "Profile fetched successfully", data=safe_profile)


@router.patch("/me")
def update_my_profile(user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated_user = UserService.update_user_profile(db, current_user.user_id, user_update)
    safe_profile = UserBase.model_validate(updated_user)
    return success_response(200, "Profile updated successfully", data=safe_profile)
