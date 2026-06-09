from uuid import UUID
import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from application.core.config import settings
from application.core.exceptions import UnauthorizedUserException, UserNotFoundException, BadRequestException
from application.db.dependencies import get_db
from application.repositories.user_repo import UserRepository
from application.models.users import User
from application.utils.logger import collector_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        user_info: dict = payload.get("user")
        if not user_info or not isinstance(user_info, dict):
            collector_logger.error("Token payload does not contain a valid subject dictionary.")
            raise UnauthorizedUserException(error_message="Invalid token payload structure")

        user_id_str = user_info.get("user_id")
        if not user_id_str:
            collector_logger.error("Token payload missing user_id.")
            raise UnauthorizedUserException(error_message="Invalid token payload")

        user_id = UUID(user_id_str)

    except jwt.ExpiredSignatureError:
        collector_logger.warning("Attempted access with expired token.")
        raise UnauthorizedUserException(error_message="Token has expired")

    except (jwt.InvalidTokenError, ValueError) as e:
        collector_logger.warning(f"Attempted access with invalid token: {e}")
        raise UnauthorizedUserException(error_message="Invalid token")

    user = UserRepository.get_user_by_id(db, user_id=user_id)
    if not user:
        collector_logger.warning(f"Token valid but user {user_id} not found in DB.")
        raise UserNotFoundException(error_message="User not found")

    collector_logger.info(f"User authenticated successfully via token: {user.email_id}")
    return user


def get_current_tenant(request: Request, current_user: User = Depends(get_current_user)) -> UUID:
    tenant_id_str = request.headers.get("x-tenant-id")

    if not tenant_id_str:
        if current_user.default_tenant:
            return current_user.default_tenant
        raise BadRequestException("x-tenant-id header is required")

    try:
        tenant_id = UUID(tenant_id_str)
    except ValueError:
        raise BadRequestException("Invalid x-tenant-id format")

    if str(tenant_id) not in current_user.tenant_lists:
        raise UnauthorizedUserException("You do not have access to this tenant")

    return tenant_id
