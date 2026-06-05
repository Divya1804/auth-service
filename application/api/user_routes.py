from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.db.dependencies import get_db
from application.schemas.users import UserCreate, UserLogin, UserUpdate, UserBase
from application.services.user_service import UserService
from application.utils.response import success_response
from application.api.dependencies import get_current_user
from application.models.users import User

router = APIRouter(prefix="/users")


@router.post("/signup")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    result = UserService.register_user(db, user_in)
    return success_response(201, "User registered successfully", data=result)


@router.post("/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    result = UserService.authenticate_user(db, user_login)
    return success_response(200, "Login successful", data=result)


@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    safe_profile = UserBase.model_validate(current_user)
    return success_response(200, "Profile fetched successfully", data=safe_profile)


@router.patch("/me")
def update_my_profile(user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated_user = UserService.update_user_profile(db, current_user.user_id, user_update)
    safe_profile = UserBase.model_validate(updated_user)
    return success_response(200, "Profile updated successfully", data=safe_profile)
