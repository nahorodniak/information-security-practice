from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Сувора політика для API (віддає лише JSON): браузеру заборонено завантажувати будь-що
API_CSP = "default-src 'none'; frame-ancestors 'none'"

# Swagger UI (/docs) та ReDoc (/redoc) вантажать JS/CSS з CDN і мають inline-скрипт,
# тому для них — окрема, послаблена політика (лише для сторінок документації)
DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.redoc.ly; "
    "worker-src 'self' blob:; "
    "frame-ancestors 'none'"
)
DOCS_PATHS = ("/docs", "/redoc")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        is_docs = request.url.path.startswith(DOCS_PATHS)
        response.headers["Content-Security-Policy"] = DOCS_CSP if is_docs else API_CSP
        response.headers["X-Frame-Options"] = "DENY"                 # Clickjacking
        response.headers["X-Content-Type-Options"] = "nosniff"       # MIME sniffing
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-XSS-Protection"] = "0"  # застарілий фільтр вимкнено (рекомендація OWASP)
        response.headers["Cache-Control"] = "no-store"               # не кешувати токени/дані
        return response
