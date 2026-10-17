"""FastAPI application entrypoint for CareerShield AI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import check_database_health

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("careershield.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]")
    logger.info(f"Active database configured engine: {settings.database_engine_name}")

    # Inspect initial database connectivity
    db_health = check_database_health()
    if db_health["connected"]:
        logger.info(
            f"Successfully connected to database ({settings.database_engine_name}) in {db_health['latency_ms']}ms."
        )
    else:
        logger.warning(
            f"Database connection could not be established at startup: {db_health['error']}. "
            f"Health endpoint will report 'degraded' until database is available."
        )

    yield

    logger.info(f"Shutting down {settings.APP_NAME}.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Job Opportunity Verification & Career-Risk Analysis API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware restricted to configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Sanitize internal errors to prevent leaking database credentials or stack traces."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "status": "error",
        },
    )


# Root landing endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
    }


# Mount API v1 router
app.include_router(api_v1_router, prefix="/api/v1")
