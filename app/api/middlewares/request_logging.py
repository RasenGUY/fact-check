import uuid
import time
from fastapi import Request
from structlog.contextvars import clear_contextvars, bind_contextvars
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging API requests and responses.

    Logs request method, path, status code, and duration.
    Adds a unique request ID to each request.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process and log request/response.

        Args:
            request: Incoming request.
            call_next: Next middleware in chain.

        Returns:
            Response from next middleware.
        """
        clear_contextvars()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        status_code = 500  # default to internal server error
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error("Request error", error=str(e))
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            bind_contextvars(status_code=status_code, duration_ms=duration_ms)

            if status_code < 400:
                logger.info("Request success")
            else:
                logger.error("Request failed", status_code=status_code)

        response.headers["X-Request-ID"] = request_id
        return response
