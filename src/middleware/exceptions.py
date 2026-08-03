"""
Exception Handling Middleware.

Catches all unhandled exceptions occurring inside endpoint routers, logs them
with full stack traces, and serves clean JSON error structures to clients.
"""

import logging
import traceback
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from src.core.logging_config import request_id_ctx_var

logger = logging.getLogger("api.exception")


class ExceptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware targeting root-level exception safety.
    
    Prevents exposure of sensitive code paths/stack traces to consumers
    by standardizing HTTP 500 error outputs with the active Request ID.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = request_id_ctx_var.get() or "SYS"
            
            # Formulate detailed log message with trace data
            logger.error(
                "Unhandled error caught in middleware for %s %s (Request ID: %s): %s\n%s",
                request.method,
                request.url.path,
                request_id,
                str(exc),
                traceback.format_exc()
            )

            # Build sanitized JSON response for HTTP 500
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An unexpected error occurred. Please try again later.",
                    "request_id": request_id,
                    "error": exc.__class__.__name__
                }
            )
