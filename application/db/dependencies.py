from application.db.session import SessionLocal
from application.utils.logger import auth_logger


def get_db():
    with SessionLocal() as db:
        try:
            auth_logger.info("Connecting to DB server...")
            yield db
        finally:
            auth_logger.info("Closing DB server...")
            db.close()
