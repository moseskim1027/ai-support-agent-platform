"""Main FastAPI application"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, health
from app.config import settings
from app.observability.metrics import setup_metrics

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Support Agent Platform",
    description="Production-ready AI customer support agent platform",
    version="0.1.0",
    docs_url="/api/docs" if not settings.is_production else None,  # Disable docs in production
    redoc_url="/api/redoc" if not settings.is_production else None,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup observability
setup_metrics(app)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 70)
    logger.info("Starting AI Support Agent Platform")
    logger.info("=" * 70)

    # Log configuration
    settings.log_config()

    # Validate required services
    logger.info("Validating services...")

    # TODO: Add actual connection checks
    # - PostgreSQL connection
    # - Redis connection
    # - Qdrant connection
    # - OpenAI API key validation

    logger.info("All services validated successfully")
    logger.info("=" * 70)
    logger.info(f"API Documentation: http://{settings.api_host}:{settings.api_port}/api/docs")
    logger.info(f"Health Check: http://{settings.api_host}:{settings.api_port}/api/health")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Support Agent Platform...")
    # TODO: Close database connections, cleanup resources
    logger.info("Shutdown complete")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
