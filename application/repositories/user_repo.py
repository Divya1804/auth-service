from uuid import UUID

from pydantic import EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql import expression

from application.models.users import User
from application.schemas.users import UserCreate


class UserRepository:

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User | None:
        stmt = select(User).where(expression.true() & User.user_id == user_id)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_user_by_email(db: Session, email: EmailStr) -> User | None:
        stmt = select(User).where(expression.true() & User.email_id == email)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User | None:
        stmt = select(User).where(expression.true() & User.username == username)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        # Note: The password in user_in MUST be pre-hashed by the service layer
        # before passing it to this repository method.
        user_data = user_in.model_dump()
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_user(db: Session, db_user: User, update_data: dict) -> User:
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: UUID) -> bool:
        db_user = UserRepository.get_user_by_id(db, user_id)
        if db_user:
            db.delete(db_user)
            db.commit()
            return True
        return False
