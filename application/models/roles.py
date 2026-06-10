import uuid
from sqlalchemy import Column, String, JSON, Uuid
from application.db.session import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    permissions = Column(JSON, default=list, nullable=False)
