from application.db.session import SessionLocal
from application.utils.logger import collector_logger


def get_db():
    with SessionLocal() as db:
        try:
            collector_logger.info("Connecting to DB server...")
            yield db
        finally:
            collector_logger.info("Closing DB server...")
            db.close()
