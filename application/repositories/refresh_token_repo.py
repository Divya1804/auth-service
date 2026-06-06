import uuid
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_
from sqlalchemy.sql import expression

from application.models.refresh_tokens import RefreshToken
from application.utils.time_ist import get_ist_now


class RefreshTokenRepository:

    @staticmethod
    def create_refresh_token(
        db: Session,
        user_id: UUID,
        tenant_id: UUID | None,
        token_hash: str,
        expires_at: datetime,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        token_id: UUID | None = None,
    ) -> RefreshToken:
        db_token = RefreshToken(
            id=token_id or uuid.uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    @staticmethod
    def get_token_by_id(db: Session, token_id: UUID) -> RefreshToken | None:
        stmt = select(RefreshToken).where(expression.true() & RefreshToken.id == token_id)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_token_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(expression.true() & RefreshToken.token_hash == token_hash)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def revoke_token(db: Session, token_id: UUID) -> RefreshToken | None:
        token = RefreshTokenRepository.get_token_by_id(db, token_id)
        if token:
            token.revoked_at = get_ist_now()
            token.last_used_at = get_ist_now()
            db.add(token)
            db.commit()
            db.refresh(token)
        return token

    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: UUID) -> None:
        stmt = update(RefreshToken).where(and_(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))).values(revoked_at=get_ist_now())
        db.execute(stmt)
        db.commit()

    @staticmethod
    def update_token_use(db: Session, token_id: UUID) -> RefreshToken | None:
        token = RefreshTokenRepository.get_token_by_id(db, token_id)
        if token:
            now = get_ist_now()
            token.last_used_at = now
            token.revoked_at = now  # Revoked on first use as part of Refresh Token Rotation
            db.add(token)
            db.commit()
            db.refresh(token)
        return token
