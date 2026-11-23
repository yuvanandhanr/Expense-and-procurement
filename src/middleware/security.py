"""
Security Headers Middleware.

Injects crucial HTTP headers to enhance standard browser security
and protect the enterprise application against common attack vectors.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that appends security headers to outgoing responses.
    
    Protects against Clickjacking, MIME sniffing, XSS, and forces HTTPS.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # 1. Prevent Clickjacking - allow framing for legitimate document/receipt previews within the app
        if request.url.path.startswith("/api/v1/expenses/receipts") or request.url.path.startswith("/uploads"):
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        else:
            response.headers["X-Frame-Options"] = "DENY"

        # 2. Prevent MIME Sniffing - force browser to obey Content-Type header
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 3. Enable Browser XSS Filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 4. Strict Transport Security (HSTS) - force SSL connections (2 years duration)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"

        # 5. Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 6. Content Security Policy (Basic defaults that allow OpenAPI / Swagger UI to function)
        # We allow self and default-src, style-src is relaxed for Swagger inline styles
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob: https://fastapi.tiangolo.com; "
            "frame-src 'self' data: blob:; "
            "object-src 'self' data: blob:;"
        )

        return response
