from typing import Any
from fastapi.responses import JSONResponse

def success_response(data: Any, message: str = "Success") -> JSONResponse:
    """
    Return a standardized successful API JSONResponse.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": message,
            "data": data
        }
    )

def error_response(message: str, status_code: int = 400) -> JSONResponse:
    """
    Return a standardized error API JSONResponse.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": message
        }
    )
