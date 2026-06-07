from fastapi import APIRouter, Depends, Request, Response, BackgroundTasks
from sqlalchemy.orm import Session

from application.db.dependencies import get_db
from application.schemas.users import UserCreate, UserLogin, UserUpdate, UserBase
from application.services.user_service import UserService
from application.utils.response import success_response
from application.api.dependencies import get_current_user
from application.models.users import User
from application.core.config import settings
from application.core.exceptions import UnauthorizedUserException
from application.utils.email import EmailService

router = APIRouter(prefix="/users")


def set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


@router.post("/signup")
def register(
    request: Request,
    background_tasks: BackgroundTasks,
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_name = request.headers.get("x-device-name")

    result, refresh_token, raw_token = UserService.register_user(db, user_in, device_name=device_name, ip_address=ip_address, user_agent=user_agent)

    # Construct verification URL
    base_url = str(request.base_url).rstrip("/")
    verification_url = f"{base_url}/api/v1/users/verify-email?token={raw_token}"

    # Asynchronously dispatch email
    background_tasks.add_task(
        EmailService.send_verification_email,
        email_to=user_in.email_id,
        username=user_in.username,
        verification_url=verification_url,
    )

    response = success_response(201, "User registered successfully. Please verify your email.", data=result)
    set_refresh_cookie(response, refresh_token)
    return response


@router.post("/login")
def login(request: Request, user_login: UserLogin, db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_name = request.headers.get("x-device-name")

    result, refresh_token = UserService.authenticate_user(db, user_login, device_name=device_name, ip_address=ip_address, user_agent=user_agent)
    response = success_response(200, "Login successful", data=result)
    set_refresh_cookie(response, refresh_token)
    return response


@router.post("/refresh")
def refresh_token(request: Request, db: Session = Depends(get_db)):
    refresh_token_str = request.cookies.get("refresh_token")
    if not refresh_token_str:
        raise UnauthorizedUserException(message="Authentication required", error_message="Refresh token is missing")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_name = request.headers.get("x-device-name")

    result, new_refresh_token = UserService.rotate_refresh_token(
        db,
        refresh_token_str=refresh_token_str,
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    response = success_response(200, "Token refreshed successfully", data=result)
    set_refresh_cookie(response, new_refresh_token)
    return response


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    refresh_token_str = request.cookies.get("refresh_token")
    response = success_response(200, "Logout successful")
    if not refresh_token_str:
        return response

    UserService.revoke_refresh_token(db, refresh_token_str=refresh_token_str)
    response.delete_cookie(key="refresh_token")
    return response


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    UserService.verify_user_email(db, token_str=token)
    return success_response(200, "Email verified successfully. Your account is now active.")


@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    safe_profile = UserBase.model_validate(current_user)
    return success_response(200, "Profile fetched successfully", data=safe_profile)


@router.patch("/me")
def update_my_profile(user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated_user = UserService.update_user_profile(db, current_user.user_id, user_update)
    safe_profile = UserBase.model_validate(updated_user)
    return success_response(200, "Profile updated successfully", data=safe_profile)
