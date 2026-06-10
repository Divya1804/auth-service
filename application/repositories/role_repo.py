from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql import expression

from application.models.roles import Role


class RoleRepository:
    @staticmethod
    def get_role_by_name(db: Session, name: str) -> Role | None:
        stmt = select(Role).where(expression.true() & Role.name == name)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_all_roles(db: Session) -> list[Role]:
        stmt = select(Role)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def create_role(db: Session, name: str, permissions: list[str]) -> Role:
        role = Role(name=name, permissions=permissions)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
