"""
Freelancer LeadTools - Free Marketing Calculators

A collection of free calculators for lead generation.
No authentication required - completely public API.

Configuration is loaded from environment variables via app/config.py
Copy .env.example to .env and update for your environment.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from app.config import settings
from app.routes import api_router

# Configure logging based on settings
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("freelancer_leadtools")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Freelancer LeadTools API")
    yield
    logger.info("Shutting down Freelancer LeadTools API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Free calculators for freelancers and agencies",
        version=settings.app_version,
        lifespan=lifespan,
        openapi_tags=[
            {"name": "individuals", "description": "Calculators for individual freelancers"},
            {"name": "agencies", "description": "Calculators for agencies"},
            {"name": "shared", "description": "Calculators for both"},
            {"name": "leads", "description": "Lead capture endpoints"},
        ],
    )

    # CORS - configure based on settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Include router
    app.include_router(api_router)

    # Health check
    @app.get("/healthz", tags=["health"])
    async def healthz():
        return {"status": "ok"}

    # Root endpoint
    @app.get("/", tags=["health"], response_class=HTMLResponse)
    async def root():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Freelancer LeadTools</title>
        </head>
        <body>
            <h1>Freelancer LeadTools API</h1>
            <p>Free calculators for freelancers and agencies</p>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/calculators/burnout">Burnout Calculator</a></li>
                <li><a href="/calculators/rate">Rate Calculator</a></li>
                <li><a href="/calculators/agency-profit">Agency Profit Calculator</a></li>
            </ul>
        </body>
        </html>
        """

    # Custom exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred",
                }
            },
        )

    return app


app = create_app()
