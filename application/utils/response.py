from typing import Any
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def success_response(code: int, message: str, data: Any = None) -> JSONResponse:
    content = {
        "code": code,
        "success": True,
        "message": message,
    }
    if data is not None:
        content["data"] = jsonable_encoder(data)

    return JSONResponse(status_code=code, content=content)


def error_response(code: int, message: str, error_code: str, error_message: Any) -> JSONResponse:
    content = {"code": code, "success": False, "message": message, "error": {"code": error_code, "message": error_message}}
    return JSONResponse(status_code=code, content=content)
