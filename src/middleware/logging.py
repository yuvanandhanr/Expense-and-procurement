"""
Logging Middleware.

Intercepts requests to log execution durations, endpoints, request status,
and errors in a centralized format.
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Use a specific logger category for API request tracking
logger = logging.getLogger("api.request")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log details of incoming HTTP requests and outgoing responses.
    
    Captures duration, HTTP method, client coordinates, and status code.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()

        method = request.method
        url = str(request.url.path)
        client_host = request.client.host if request.client else "unknown"

        # Log initial request parameters
        logger.info(
            "Request started: %s %s - Client: %s",
            method,
            url,
            client_host
        )

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time

            # Log completion metrics
            logger.info(
                "Request completed: %s %s - Status: %d - Duration: %.4fs",
                method,
                url,
                response.status_code,
                duration
            )
            return response
        except Exception as exc:
            duration = time.perf_counter() - start_time
            logger.error(
                "Request failed during execution: %s %s - Error: %s - Duration: %.4fs",
                method,
                url,
                str(exc),
                duration
            )
            raise exc
