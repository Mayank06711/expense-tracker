import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    field_errors = {}
    for err in errors:
        loc = err.get("loc", [])
        field = loc[-1] if loc else "unknown"
        field_errors[str(field)] = err.get("msg", "Invalid value")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation failed",
            "error_code": "VALIDATION_ERROR",
            "metadata": {"fields": field_errors},
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_code": "HTTP_ERROR",
            "metadata": {},
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "metadata": {},
        },
    )
