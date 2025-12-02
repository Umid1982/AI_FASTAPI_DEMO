from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication (аналог VerifyTelegramApiKey)."""
    
    def __init__(self, app: ASGIApp, api_key_header: str = "X-API-KEY"):
        super().__init__(app)
        self.api_key_header = api_key_header
        self.valid_api_key = settings.api_key
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for health checks, docs, and metrics
        if request.url.path in ["/health", "/docs", "/openapi.json", "/", "/metrics", "/info"]:
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get(self.api_key_header)
        
        if not api_key:
            logger.warning("Missing API key", path=request.url.path, ip=request.client.host)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"success": False, "message": "Missing API key"}
            )
        
        if api_key != self.valid_api_key:
            logger.warning("Invalid API key", path=request.url.path, ip=request.client.host)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"success": False, "message": "Invalid API key"}
            )
        
        logger.info("API key validated", path=request.url.path, ip=request.client.host)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers (аналог SecurityHeadersMiddleware)."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with proper configuration."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.allowed_origins = settings.cors_origins
        self.allowed_methods = settings.cors_methods
        self.allowed_headers = settings.cors_headers
    
    async def dispatch(self, request: Request, call_next):
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = JSONResponse(content={})
        else:
            response = await call_next(request)
        
        # Add CORS headers
        origin = request.headers.get("origin")
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next):
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            client_ip=request.client.host if request.client else None
        )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as e:
            logger.error(
                "HTTP exception",
                status_code=e.status_code,
                detail=e.detail,
                path=request.url.path
            )
            return JSONResponse(
                status_code=e.status_code,
                content={"success": False, "message": e.detail}
            )
        except Exception as e:
            logger.error(
                "Unhandled exception",
                error=str(e),
                path=request.url.path,
                exc_info=True
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "message": "Internal server error",
                    "error_code": "INTERNAL_ERROR"
                }
            )


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics."""
    
    async def dispatch(self, request: Request, call_next):
        import time
        from app.core.metrics import http_requests_total, http_request_duration_seconds
        
        method = request.method
        path = request.url.path
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        status_code = response.status_code
        duration = time.time() - start_time
        
        http_requests_total.labels(method=method, endpoint=path, status=status_code).inc()
        http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration)
        
        return response
