from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from sqlalchemy.sql import expression

from application.models.verification_tokens import VerificationToken, TokenPurpose


class VerificationTokenRepository:

    @staticmethod
    def create_verification_token(
        db: Session,
        user_id: UUID,
        email_id: str,
        token_hash: str,
        purpose: TokenPurpose,
        expires_at: datetime,
    ) -> VerificationToken:
        db_token = VerificationToken(
            user_id=user_id,
            email_id=email_id,
            token_hash=token_hash,
            purpose=purpose,
            expires_at=expires_at,
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    @staticmethod
    def get_token_by_hash(db: Session, token_hash: str, purpose: TokenPurpose) -> VerificationToken | None:
        stmt = select(VerificationToken).where(
            and_(VerificationToken.token_hash == token_hash, VerificationToken.purpose == purpose)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def delete_token(db: Session, token_id: UUID) -> bool:
        stmt = select(VerificationToken).where(expression.true() & VerificationToken.id == token_id)
        db_token = db.execute(stmt).scalars().first()
        if db_token:
            db.delete(db_token)
            db.commit()
            return True
        return False
