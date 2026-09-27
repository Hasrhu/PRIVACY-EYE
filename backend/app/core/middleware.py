"""
Custom middleware: Rate limiting and Request ID injection.
"""
import time
import uuid
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory sliding-window rate limiter.
    For production, replace with Redis-backed limiter (e.g. slowapi).
    """

    def __init__(self, app, calls: int = 30, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self._requests: dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check and high-frequency live camera frames
        if request.url.path in ["/", "/api/v1/health"] or request.url.path.startswith("/api/v1/live/frame"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.period

        # Prune old requests
        self._requests[client_ip] = [t for t in self._requests[client_ip] if t > window_start]

        if len(self._requests[client_ip]) >= self.calls:
            logger.warning("Rate limit exceeded", client_ip=client_ip)
            return Response(
                content='{"detail":"Rate limit exceeded. Please slow down."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.period)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
