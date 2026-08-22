"""
SIH26162 — FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance,
sets up CORS middleware, and includes all API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_v1_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
