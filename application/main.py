from fastapi import FastAPI, Request

from application.db.session import Base, engine
from application.api.user_routes import router as users_router
from application.api.tenant_routes import router as tenants_router
from application.core.exceptions import AppException
from application.utils.response import error_response

app = FastAPI()


@app.on_event("startup")
def create_tables():
    """
    Creates DB tables on startup
    """
    Base.metadata.create_all(bind=engine)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return error_response(code=exc.status_code, message=exc.message, error_code=exc.error_code, error_message=exc.error_message)


app.include_router(users_router, prefix="/api/v1", tags=["Users API"])
app.include_router(tenants_router, prefix="/api/v1", tags=["Tenants API"])


@app.get("/health")
def health_check():
    return {"message": "Service is Healthy"}
