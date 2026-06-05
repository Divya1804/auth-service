from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from application.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_size=20, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine, class_=Session)

Base = declarative_base()
