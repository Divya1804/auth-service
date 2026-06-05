from uuid import UUID
from sqlalchemy.orm import Session

from application.repositories.user_repo import UserRepository
from application.schemas.users import UserCreate, UserLogin, UserUpdate, UserResponse, Token, UserBase
from application.utils.security import get_password_hash, verify_password, create_access_token
from application.core.exceptions import UserAlreadyExistsException, InvalidCredentialsException, UserNotFoundException
from application.utils.logger import collector_logger


class UserService:

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> UserResponse:
        # 1. Check for email duplication
        if UserRepository.get_user_by_email(db, email=user_in.email_id):
            collector_logger.error(f"Registration failed: Email {user_in.email_id} already exists.")
            raise UserAlreadyExistsException("User already exists with this email id")

        # 2. Check for username duplication
        if UserRepository.get_user_by_username(db, username=user_in.username):
            collector_logger.error(f"Registration failed: Username {user_in.username} already exists.")
            raise UserAlreadyExistsException("User already exists with this username")

        # 3. Hash password
        user_in.password = get_password_hash(user_in.password)

        # 4. Save to DB
        new_user = UserRepository.create_user(db, user_in=user_in)
        collector_logger.info(f"User successfully registered: {new_user.email_id}")

        # 5. Generate Access Token (Ensuring user_id is a string)
        token_str = create_access_token(subject={"user_id": str(new_user.user_id), "email_id": new_user.email_id, "username": new_user.username})
        token = Token(access_token=token_str, token_type="bearer")

        # 6. Format Response
        base_user = UserBase.model_validate(new_user)
        response = UserResponse(**base_user.model_dump(), tokens=token)

        return response

    @staticmethod
    def authenticate_user(db: Session, user_login: UserLogin) -> UserResponse:
        # 1. Look up user by email
        user = UserRepository.get_user_by_email(db, email=user_login.email_id)
        if not user:
            collector_logger.error(f"Login failed: User with email {user_login.email_id} not found.")
            raise InvalidCredentialsException("Invalid email or password")

        # 2. Verify password hash
        if not verify_password(user_login.password, user.password):
            collector_logger.error(f"Login failed: Incorrect password for email {user_login.email_id}.")
            raise InvalidCredentialsException("Invalid email or password")

        # 3. Generate Access Token
        token_str = create_access_token(subject={"user_id": str(user.user_id), "email_id": user.email_id, "username": user.username})
        token = Token(access_token=token_str, token_type="bearer")

        # 4. Format Response
        base_user = UserBase.model_validate(user)
        response = UserResponse(**base_user.model_dump(), tokens=token)

        collector_logger.info(f"User logged in successfully: {user.email_id}")
        return response

    @staticmethod
    def update_user_profile(db: Session, user_id: UUID, user_update: UserUpdate):
        db_user = UserRepository.get_user_by_id(db, user_id)
        if not db_user:
            collector_logger.error(f"Profile update failed: User {user_id} not found.")
            raise UserNotFoundException()

        # exclude_unset=True ensures we only update fields that were actually provided in the request
        update_data = user_update.model_dump(exclude_unset=True)
        updated_user = UserRepository.update_user(db, db_user, update_data)

        collector_logger.info(f"User profile updated successfully: {updated_user.email_id}")
        return updated_user
