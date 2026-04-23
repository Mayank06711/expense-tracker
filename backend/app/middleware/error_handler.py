import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


def _req_meta(request: Request) -> dict:
    return {
        "request_id": getattr(request.state, "request_id", None),
        "timestamp": getattr(request.state, "timestamp", None),
    }


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    field_errors = {}
    for err in errors:
        loc = err.get("loc", [])
        field = loc[-1] if loc else "unknown"
        msg = err.get("msg", "Invalid value")
        # Strip "Value error, " prefix for cleaner messages
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        field_errors[str(field)] = msg

    # Build a human-readable summary from field errors
    summary_parts = [f"{field}: {msg}" for field, msg in field_errors.items()]
    summary = "; ".join(summary_parts)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": summary,
            "error_code": "VALIDATION_ERROR",
            "metadata": {"fields": field_errors, **_req_meta(request)},
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_code": "HTTP_ERROR",
            "metadata": _req_meta(request),
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
            "metadata": _req_meta(request),
        },
    )
