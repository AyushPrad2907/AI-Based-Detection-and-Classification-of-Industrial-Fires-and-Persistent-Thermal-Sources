"""
SIH26162 — FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance,
sets up CORS middleware, and includes all API routers.
"""

import logging
import sys
from pathlib import Path

# Ensure 'backend' directory and repository root are present in sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(1, str(_REPO_ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, OperationalError

from app.config import settings
from app.api.v1.router import api_v1_router

logger = logging.getLogger("api")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings.postgres_password == 'change_me_in_production' and settings.environment != 'development':
        logger.critical("Default database password in use in non-development environment!")

    app = FastAPI(
        title="SIH26162 — Industrial Fire & Thermal AI Detector",
        description=(
            "AI-Based Detection and Classification of Industrial Fires "
            "and Persistent Thermal Sources Using NASA FIRMS, OSM & Satellite Data."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # -------------------------------------------------------------------------
    # CORS Middleware
    # In production, restrict origins to your frontend domain.
    # -------------------------------------------------------------------------
    origins = ["http://localhost:5173", "http://localhost:3000"] if settings.environment == "development" else [settings.frontend_url]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials="*" not in origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------------------------------------------------
    # Database Exception Handlers
    # -------------------------------------------------------------------------
    @app.exception_handler(OperationalError)
    @app.exception_handler(DBAPIError)
    @app.exception_handler(OSError)
    async def db_exception_handler(request: Request, exc: Exception):
        logger.error(f"Database operational error on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Database connection or query execution error.",
                "error": str(exc),
            },
        )

    # -------------------------------------------------------------------------
    # Include API Routers
    # -------------------------------------------------------------------------
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


# Create the application instance
app = create_app()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — basic service information."""
    return {
        "service": "SIH26162 — Industrial Fire & Thermal AI Detector",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
