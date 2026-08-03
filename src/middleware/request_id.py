"""
Request ID Middleware.

Ensures every incoming request is assigned a unique Request ID (correlation ID)
which is propagated across log contexts and returned in downstream headers.
"""

import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from src.core.logging_config import request_id_ctx_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware responsible for extracting or generating a unique Request ID.
    
    This ID is stored in the context-local variable for logging and attached to response headers.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check if request ID was supplied by upstream reverse proxies (e.g. AWS ALB or CloudFront)
        request_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
        
        if not request_id:
            request_id = str(uuid.uuid4())

        # Set the request ID in context-local storage
        token = request_id_ctx_var.set(request_id)
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        finally:
            # Guarantee the context variable is reset to prevent leakages
            request_id_ctx_var.reset(token)

        # Append correlation ID to response headers for tracking client-side
        response.headers["X-Request-ID"] = request_id
        return response
