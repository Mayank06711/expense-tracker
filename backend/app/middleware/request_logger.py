import logging
import time
import traceback
import uuid
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.request")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        request_id = str(uuid.uuid4())[:8]
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""

        # Attach request_id so routes can access it
        request.state.request_id = request_id
        request.state.timestamp = datetime.now(timezone.utc).isoformat()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000

            # Inject request_id into response headers (non-blocking)
            response.headers["X-Request-ID"] = request_id

            logger.info(
                "[%s] %s %s%s -> %d (%.1fms)",
                request_id,
                method,
                path,
                f"?{query}" if query else "",
                response.status_code,
                duration_ms,
            )
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            tb = traceback.extract_tb(exc.__traceback__)
            if tb:
                last_frame = tb[-1]
                location = f"{last_frame.filename}:{last_frame.lineno} in {last_frame.name}"
            else:
                location = "unknown"

            logger.error(
                "[%s] %s %s -> 500 (%.1fms) | %s: %s | at %s",
                request_id,
                method,
                path,
                duration_ms,
                type(exc).__name__,
                str(exc),
                location,
            )
            raise
