from datetime import timedelta
import uuid
from uuid import UUID
import jwt
from sqlalchemy.orm import Session

from application.repositories.user_repo import UserRepository
from application.repositories.refresh_token_repo import RefreshTokenRepository
from application.repositories.verification_token_repo import VerificationTokenRepository
from application.models.verification_tokens import TokenPurpose
from application.models.users import UserStatus
from application.schemas.users import UserCreate, UserLogin, UserUpdate, UserResponse, Token, UserBase, ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest, ChangeEmailRequest
from fastapi import BackgroundTasks
from application.utils.email import EmailService
from application.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token_string,
    generate_verification_token,
)
from application.core.exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserNotFoundException,
    UnauthorizedUserException,
    BadRequestException,
)
from application.utils.logger import auth_logger
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
    ) -> tuple[Token, str]:
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

        token = Token(access_token=access_token_str, token_type="bearer")
        return token, refresh_token_str

    @staticmethod
    def register_user(
        db: Session,
        user_in: UserCreate,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[UserResponse, str, str]:
        # 1. Check for email duplication
        if UserRepository.get_user_by_email(db, email=user_in.email_id):
            auth_logger.error(f"Registration failed: Email {user_in.email_id} already exists.")
            raise UserAlreadyExistsException("User already exists with this email id")

        # 2. Check for username duplication
        if UserRepository.get_user_by_username(db, username=user_in.username):
            auth_logger.error(f"Registration failed: Username {user_in.username} already exists.")
            raise UserAlreadyExistsException("User already exists with this username")

        # 3. Hash password
        user_in.password = get_password_hash(user_in.password)

        # 4. Save to DB (Defaults to status = INACTIVE, is_verified = False)
        new_user = UserRepository.create_user(db, user_in=user_in)
        auth_logger.info(f"User successfully registered: {new_user.email_id}")

        # 5. Generate Access & Refresh Tokens
        token, refresh_token_str = UserService._create_token_pair(
            db=db,
            user=new_user,
            tenant_id=new_user.default_tenant,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 6. Generate Verification Token
        raw_verification_token = generate_verification_token()
        token_hash = hash_token_string(raw_verification_token)
        expires_at = get_ist_now() + timedelta(hours=24)  # Token valid for 24 hours

        VerificationTokenRepository.create_verification_token(
            db=db,
            user_id=new_user.user_id,
            email_id=new_user.email_id,
            token_hash=token_hash,
            purpose=TokenPurpose.EMAIL_VERIFICATION,
            expires_at=expires_at,
        )

        # 7. Format Response
        base_user = UserBase.model_validate(new_user)
        response = UserResponse(**base_user.model_dump(), tokens=token)

        return response, refresh_token_str, raw_verification_token

    @staticmethod
    def authenticate_user(
        db: Session,
        user_login: UserLogin,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[UserResponse, str]:
        # 1. Look up user by email
        user = UserRepository.get_user_by_email(db, email=user_login.email_id)
        if not user:
            auth_logger.error(f"Login failed: User with email {user_login.email_id} not found.")
            raise InvalidCredentialsException("Invalid email or password")

        # 2. Verify password hash
        if not verify_password(user_login.password, user.password):
            auth_logger.error(f"Login failed: Incorrect password for email {user_login.email_id}.")
            raise InvalidCredentialsException("Invalid email or password")

        # 3. Generate Access & Refresh Tokens
        token, refresh_token_str = UserService._create_token_pair(
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

        auth_logger.info(f"User logged in successfully: {user.email_id}")
        return response, refresh_token_str

    @staticmethod
    def verify_user_email(db: Session, token_str: str) -> None:
        token_hash = hash_token_string(token_str)
        db_token = VerificationTokenRepository.get_token_by_hash(db, token_hash=token_hash, purpose=TokenPurpose.EMAIL_VERIFICATION)

        if not db_token:
            auth_logger.error("Email verification failed: Token not found.")
            raise BadRequestException("Invalid or expired verification token")

        # Check expiration
        if db_token.expires_at < get_ist_now():
            auth_logger.warning(f"Email verification failed: Token {db_token.id} has expired.")
            # Cleanup expired token
            VerificationTokenRepository.delete_token(db, db_token.id)
            raise BadRequestException("Verification token has expired")

        # Fetch User
        user = UserRepository.get_user_by_id(db, user_id=db_token.user_id)
        if not user:
            auth_logger.error(f"Verification token valid but user {db_token.user_id} not found.")
            raise UserNotFoundException()

        # Update User status
        UserRepository.update_user(db, user, {"is_verified": True, "status": UserStatus.ACTIVE})

        # Cleanup verification token
        VerificationTokenRepository.delete_token(db, db_token.id)
        auth_logger.info(f"User email verified and activated: {user.email_id}")

    @staticmethod
    def rotate_refresh_token(
        db: Session,
        refresh_token_str: str,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[UserResponse, str]:
        try:
            payload = jwt.decode(refresh_token_str, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

            token_type = payload.get("type")
            if token_type != "refresh":
                auth_logger.error("Attempted token refresh with non-refresh token.")
                raise UnauthorizedUserException("Invalid token type")

            token_id_str = payload.get("jti")
            user_id_str = payload.get("sub")
            if not token_id_str or not user_id_str:
                auth_logger.error("Token payload missing required fields.")
                raise UnauthorizedUserException("Invalid token payload")

            token_id = uuid.UUID(token_id_str)
            user_id = uuid.UUID(user_id_str)

        except jwt.ExpiredSignatureError:
            auth_logger.warning("Attempted refresh with expired token.")
            raise UnauthorizedUserException(message="Token expired", error_message="Token has expired")
        except (jwt.InvalidTokenError, ValueError) as e:
            auth_logger.warning(f"Attempted refresh with invalid token: {e}")
            raise UnauthorizedUserException(message="Invalid token", error_message="Invalid token structure")

        # Fetch db token
        db_token = RefreshTokenRepository.get_token_by_id(db, token_id)
        if not db_token:
            auth_logger.error(f"Refresh token {token_id} not found in database.")
            raise UnauthorizedUserException(message="Invalid token", error_message="Refresh token not found")

        # Hash check
        current_hash = hash_token_string(refresh_token_str)
        if db_token.token_hash != current_hash:
            auth_logger.error("Refresh token hash mismatch.")
            raise UnauthorizedUserException(message="Invalid token", error_message="Token signature mismatch")

        # Check expiration
        if db_token.expires_at < get_ist_now():
            auth_logger.warning(f"Refresh token {token_id} has expired in database.")
            raise UnauthorizedUserException(message="Token expired", error_message="Token has expired")

        # Replay Attack Detection
        if db_token.revoked_at is not None or db_token.last_used_at is not None:
            auth_logger.warning(f"Replay attack detected for token {token_id}! Revoking all active sessions for user {user_id}.")
            # Revoke all active sessions
            RefreshTokenRepository.revoke_all_user_tokens(db, user_id=user_id)
            raise UnauthorizedUserException(message="Session terminated", error_message="Replay attack detected. Please log in again.")

        # Retrieve User
        user = UserRepository.get_user_by_id(db, user_id=user_id)
        if not user:
            auth_logger.error(f"Refresh token valid but user {user_id} not found.")
            raise UserNotFoundException()

        # Update current token (marks as used and revoked)
        RefreshTokenRepository.update_token_use(db, token_id)

        # Retrieve tenant_id
        tenant_id_str = payload.get("tenant_id")
        tenant_id = uuid.UUID(tenant_id_str) if tenant_id_str else user.default_tenant

        # Generate new token pair
        token, new_refresh_token_str = UserService._create_token_pair(
            db=db,
            user=user,
            tenant_id=tenant_id,
            device_name=device_name or db_token.device_name,
            ip_address=ip_address or db_token.ip_address,
            user_agent=user_agent or db_token.user_agent,
        )

        base_user = UserBase.model_validate(user)
        response = UserResponse(**base_user.model_dump(), tokens=token)

        auth_logger.info(f"Successfully rotated refresh token for user: {user.email_id}")
        return response, new_refresh_token_str

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token_str: str) -> None:
        try:
            payload = jwt.decode(refresh_token_str, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            token_id_str = payload.get("jti")
            if not token_id_str:
                raise UnauthorizedUserException("Invalid token payload")
            token_id = uuid.UUID(token_id_str)
        except (jwt.InvalidTokenError, ValueError) as e:
            auth_logger.warning(f"Attempted logout with invalid token: {e}")
            raise UnauthorizedUserException(message="Invalid token", error_message="Token parsing failed")

        db_token = RefreshTokenRepository.get_token_by_id(db, token_id)
        if not db_token:
            auth_logger.warning(f"Logout token {token_id} not found in DB.")
            return

        # Hash check
        current_hash = hash_token_string(refresh_token_str)
        if db_token.token_hash != current_hash:
            auth_logger.error("Logout token hash mismatch.")
            raise UnauthorizedUserException(message="Invalid token", error_message="Token signature mismatch")

        # Mark as revoked
        RefreshTokenRepository.revoke_token(db, token_id)
        auth_logger.info(f"Successfully revoked refresh token: {token_id} for user {db_token.user_id}")

    @staticmethod
    def update_user_profile(db: Session, user_id: UUID, user_update: UserUpdate):
        db_user = UserRepository.get_user_by_id(db, user_id)
        if not db_user:
            auth_logger.error(f"Profile update failed: User {user_id} not found.")
            raise UserNotFoundException()

        # exclude_unset=True ensures we only update fields that were actually provided in the request
        update_data = user_update.model_dump(exclude_unset=True)
        updated_user = UserRepository.update_user(db, db_user, update_data)

        auth_logger.info(f"User profile updated successfully: {updated_user.email_id}")
        return updated_user

    @staticmethod
    def forgot_password(db: Session, request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
        user = UserRepository.get_user_by_email(db, request.email_id)
        if not user:
            # We don't throw an error to prevent email enumeration, just return
            auth_logger.info(f"Forgot password requested for non-existent email: {request.email_id}")
            return

        raw_reset_token = generate_verification_token()
        token_hash = hash_token_string(raw_reset_token)
        expires_at = get_ist_now() + timedelta(minutes=15)  # Short expiry for password reset

        VerificationTokenRepository.create_verification_token(
            db=db,
            user_id=user.user_id,
            email_id=user.email_id,
            token_hash=token_hash,
            purpose=TokenPurpose.FORGOT_PASSWORD,
            expires_at=expires_at,
        )

        # Dispatch email asynchronously
        background_tasks.add_task(
            EmailService.send_password_reset_email,
            email_to=user.email_id,
            username=user.first_name,
            reset_token=raw_reset_token,
        )
        auth_logger.info(f"Password reset token generated for user: {user.email_id}")

    @staticmethod
    def reset_password(db: Session, request: ResetPasswordRequest):
        token_hash = hash_token_string(request.token)

        # Verify token exists and is valid
        db_token = VerificationTokenRepository.get_token_by_hash(db, token_hash, TokenPurpose.FORGOT_PASSWORD)

        if not db_token or db_token.purpose != TokenPurpose.FORGOT_PASSWORD:
            auth_logger.error("Password reset failed: Invalid or missing token")
            raise BadRequestException("Invalid or expired reset token")

        if db_token.expires_at < get_ist_now():
            VerificationTokenRepository.delete_token(db, db_token.id)
            auth_logger.error(f"Password reset failed: Expired token for email {db_token.email_id}")
            raise BadRequestException("Invalid or expired reset token")

        user = UserRepository.get_user_by_id(db, db_token.user_id)
        if not user:
            raise UserNotFoundException("User not found")

        # Update password
        new_password_hash = get_password_hash(request.new_password)
        UserRepository.update_user(db, user, {"password": new_password_hash})

        # Delete the verification token after successful use
        VerificationTokenRepository.delete_token(db, db_token.id)

        # Revoke all active refresh tokens for security
        RefreshTokenRepository.revoke_all_user_tokens(db, user.user_id)

        auth_logger.info(f"Password reset successfully for user: {user.email_id}. All sessions revoked.")

    @staticmethod
    def change_password(db: Session, user_id: UUID, request: ChangePasswordRequest):
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            raise UserNotFoundException("User not found")

        # Verify old password
        if not verify_password(request.old_password, user.password):
            auth_logger.error(f"Change password failed: Incorrect old password for {user.email_id}.")
            raise InvalidCredentialsException("Incorrect old password")

        # if request.new_password != request.confirm_new_password:
        #     collector_logger.error(f"New password and confirm new password is not matching for {user.email_id}")
        #     raise BadRequestException("Invalid new password or confirm new password")

        # Update with new password
        new_password_hash = get_password_hash(request.new_password)
        UserRepository.update_user(db, user, {"password": new_password_hash})

        # Revoke all active refresh tokens for security
        RefreshTokenRepository.revoke_all_user_tokens(db, user.user_id)

        auth_logger.info(f"Password changed successfully for user: {user.email_id}. All sessions revoked.")

    @staticmethod
    def change_email(db: Session, user_id: UUID, request: ChangeEmailRequest, background_tasks: BackgroundTasks, base_url: str):
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            raise UserNotFoundException("User not found")

        new_email = request.new_email_id

        # Check if email is already taken
        existing_user = UserRepository.get_user_by_email(db, new_email)
        if existing_user and existing_user.user_id != user_id:
            auth_logger.error(f"Change email failed: Email {new_email} is already in use.")
            raise UserAlreadyExistsException("Email is already registered by another account")

        # Update user's email and set to unverified
        UserRepository.update_user(db, user, {"email_id": new_email, "is_verified": False})

        # Generate new verification token
        raw_verification_token = generate_verification_token()
        token_hash = hash_token_string(raw_verification_token)
        expires_at = get_ist_now() + timedelta(hours=24)

        VerificationTokenRepository.create_verification_token(
            db=db,
            user_id=user.user_id,
            email_id=new_email,
            token_hash=token_hash,
            purpose=TokenPurpose.EMAIL_VERIFICATION,
            expires_at=expires_at,
        )

        # Construct verification URL
        verification_url = f"{base_url}/api/v1/users/verify-email?token={raw_verification_token}"

        # Dispatch email asynchronously
        background_tasks.add_task(
            EmailService.send_verification_email,
            email_to=new_email,
            username=user.first_name,
            verification_url=verification_url,
        )
        auth_logger.info(f"Verification email sent to new email: {new_email}")
