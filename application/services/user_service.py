from datetime import timedelta
import uuid
from uuid import UUID
import jwt
from sqlalchemy.orm import Session

from application.repositories.user_repo import UserRepository
from application.repositories.refresh_token_repo import RefreshTokenRepository
from application.schemas.users import UserCreate, UserLogin, UserUpdate, UserResponse, Token, UserBase
from application.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token_string,
)
from application.core.exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserNotFoundException,
    UnauthorizedUserException,
)
from application.utils.logger import collector_logger
from application.core.config import settings
from application.utils.time_ist import get_ist_now


class UserService:

    @staticmethod
    def _create_token_pair(
        db: Session,
        user,
        tenant_id: UUID | None = None,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Token:
        token_id = uuid.uuid4()
        expires_at = get_ist_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Access Token payload
        subject = {"user_id": str(user.user_id), "email_id": user.email_id, "username": user.username}
        access_token_str = create_access_token(subject=subject)

        # Refresh Token payload
        refresh_token_str = create_refresh_token(user_id=user.user_id, token_id=token_id, tenant_id=tenant_id)
        token_hash = hash_token_string(refresh_token_str)

        # Create DB record
        RefreshTokenRepository.create_refresh_token(
            db=db,
            user_id=user.user_id,
            tenant_id=tenant_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            token_id=token_id,
        )

        return Token(access_token=access_token_str, refresh_token=refresh_token_str, token_type="bearer")

    @staticmethod
    def register_user(
        db: Session,
        user_in: UserCreate,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserResponse:
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

        # 5. Generate Access & Refresh Tokens
        token = UserService._create_token_pair(
            db=db,
            user=new_user,
            tenant_id=new_user.default_tenant,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 6. Format Response
        base_user = UserBase.model_validate(new_user)
        response = UserResponse(**base_user.model_dump(), tokens=token)

        return response

    @staticmethod
    def authenticate_user(
        db: Session,
        user_login: UserLogin,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserResponse:
        # 1. Look up user by email
        user = UserRepository.get_user_by_email(db, email=user_login.email_id)
        if not user:
            collector_logger.error(f"Login failed: User with email {user_login.email_id} not found.")
            raise InvalidCredentialsException("Invalid email or password")

        # 2. Verify password hash
        if not verify_password(user_login.password, user.password):
            collector_logger.error(f"Login failed: Incorrect password for email {user_login.email_id}.")
            raise InvalidCredentialsException("Invalid email or password")

        # 3. Generate Access & Refresh Tokens
        token = UserService._create_token_pair(
            db=db,
            user=user,
            tenant_id=user.default_tenant,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 4. Format Response
        base_user = UserBase.model_validate(user)
        response = UserResponse(**base_user.model_dump(), tokens=token)

        collector_logger.info(f"User logged in successfully: {user.email_id}")
        return response

    @staticmethod
    def rotate_refresh_token(
        db: Session,
        refresh_token_str: str,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserResponse:
        try:
            payload = jwt.decode(refresh_token_str, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

            token_type = payload.get("type")
            if token_type != "refresh":
                collector_logger.error("Attempted token refresh with non-refresh token.")
                raise UnauthorizedUserException("Invalid token type")

            token_id_str = payload.get("jti")
            user_id_str = payload.get("sub")
            if not token_id_str or not user_id_str:
                collector_logger.error("Token payload missing required fields.")
                raise UnauthorizedUserException("Invalid token payload")

            token_id = uuid.UUID(token_id_str)
            user_id = uuid.UUID(user_id_str)

        except jwt.ExpiredSignatureError:
            collector_logger.warning("Attempted refresh with expired token.")
            raise UnauthorizedUserException(message="Token expired", error_message="Token has expired")
        except (jwt.InvalidTokenError, ValueError) as e:
            collector_logger.warning(f"Attempted refresh with invalid token: {e}")
            raise UnauthorizedUserException(message="Invalid token", error_message="Invalid token structure")

        # Fetch db token
        db_token = RefreshTokenRepository.get_token_by_id(db, token_id)
        if not db_token:
            collector_logger.error(f"Refresh token {token_id} not found in database.")
            raise UnauthorizedUserException(message="Invalid token", error_message="Refresh token not found")

        # Hash check
        current_hash = hash_token_string(refresh_token_str)
        if db_token.token_hash != current_hash:
            collector_logger.error("Refresh token hash mismatch.")
            raise UnauthorizedUserException(message="Invalid token", error_message="Token signature mismatch")

        # Check expiration
        if db_token.expires_at < get_ist_now():
            collector_logger.warning(f"Refresh token {token_id} has expired in database.")
            raise UnauthorizedUserException(message="Token expired", error_message="Token has expired")

        # Replay Attack Detection
        if db_token.revoked_at is not None or db_token.last_used_at is not None:
            collector_logger.warning(f"Replay attack detected for token {token_id}! Revoking all active sessions for user {user_id}.")
            # Revoke all active sessions
            RefreshTokenRepository.revoke_all_user_tokens(db, user_id=user_id)
            raise UnauthorizedUserException(message="Session terminated", error_message="Replay attack detected. Please log in again.")

        # Retrieve User
        user = UserRepository.get_user_by_id(db, user_id=user_id)
        if not user:
            collector_logger.error(f"Refresh token valid but user {user_id} not found.")
            raise UserNotFoundException()

        # Update current token (marks as used and revoked)
        RefreshTokenRepository.update_token_use(db, token_id)

        # Retrieve tenant_id
        tenant_id_str = payload.get("tenant_id")
        tenant_id = uuid.UUID(tenant_id_str) if tenant_id_str else user.default_tenant

        # Generate new token pair
        new_tokens = UserService._create_token_pair(
            db=db,
            user=user,
            tenant_id=tenant_id,
            device_name=device_name or db_token.device_name,
            ip_address=ip_address or db_token.ip_address,
            user_agent=user_agent or db_token.user_agent,
        )

        base_user = UserBase.model_validate(user)
        response = UserResponse(**base_user.model_dump(), tokens=new_tokens)

        collector_logger.info(f"Successfully rotated refresh token for user: {user.email_id}")
        return response

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token_str: str) -> None:
        try:
            payload = jwt.decode(refresh_token_str, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            token_id_str = payload.get("jti")
            if not token_id_str:
                raise UnauthorizedUserException("Invalid token payload")
            token_id = uuid.UUID(token_id_str)
        except (jwt.InvalidTokenError, ValueError) as e:
            collector_logger.warning(f"Attempted logout with invalid token: {e}")
            raise UnauthorizedUserException(message="Invalid token", error_message="Token parsing failed")

        db_token = RefreshTokenRepository.get_token_by_id(db, token_id)
        if not db_token:
            collector_logger.warning(f"Logout token {token_id} not found in DB.")
            return

        # Hash check
        current_hash = hash_token_string(refresh_token_str)
        if db_token.token_hash != current_hash:
            collector_logger.error("Logout token hash mismatch.")
            raise UnauthorizedUserException(message="Invalid token", error_message="Token signature mismatch")

        # Mark as revoked
        RefreshTokenRepository.revoke_token(db, token_id)
        collector_logger.info(f"Successfully revoked refresh token: {token_id} for user {db_token.user_id}")

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
