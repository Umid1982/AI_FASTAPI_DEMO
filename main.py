from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.core.config import settings
from app.core.metrics import http_requests_total, http_request_duration_seconds, video_analysis_total
from app.core.middleware import (
    APIKeyMiddleware,
    SecurityHeadersMiddleware,
    CORSMiddleware as CustomCORSMiddleware,
    LoggingMiddleware,
    ErrorHandlingMiddleware,
    PrometheusMetricsMiddleware
)
from app.database.connection import create_tables
from app.routes.video import router as video_router
from app.routes.reports import router as reports_router
from app.utils.response_helper import success_response

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Video Analytics Microservice", version=settings.app_version)

    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down AI Video Analytics Microservice")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered video analytics microservice for real-time people detection and tracking",
    debug=settings.debug,
    lifespan=lifespan
)

# Добавляем Swagger API-key авторизацию (чтобы появился замочек 🔒)
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name=settings.x_api_key_header, auto_error=False)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "name": settings.x_api_key_header,
            "in": "header"
        }
    }
    openapi_schema["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Add middleware (order matters!)
app.add_middleware(PrometheusMetricsMiddleware)  # Prometheus metrics first
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(APIKeyMiddleware, api_key_header=settings.x_api_key_header)
app.add_middleware(CustomCORSMiddleware)

# Add CORS middleware as fallback
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Include routers
app.include_router(video_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    """Root endpoint with service information."""
    return success_response(
        data={
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "environment": settings.environment
        },
        message="AI Video Analytics Microservice is running! 🚀"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint with database connectivity."""
    from datetime import datetime
    from app.database.connection import engine
    from sqlalchemy import text
    
    # Check database connectivity
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "error"
        logger.error("Database health check failed", error=str(e))
    
    status = "healthy" if db_status == "ok" else "unhealthy"
    
    return success_response(
        data={
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status
        },
        message="Service is healthy" if status == "healthy" else "Service has issues"
    )


@app.get("/info")
async def service_info():
    """Service information endpoint."""
    return success_response(
        data={
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug,
            "features": [
                "Real-time video analysis",
                "People detection and tracking",
                "AI-powered analytics reports",
                "Heatmap generation",
                "RESTful API"
            ]
        },
        message="Service information"
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


