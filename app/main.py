"""
Freelancer LeadTools - Free Marketing Calculators

A collection of free calculators for lead generation.
No authentication required - completely public API.

SECURITY FEATURES:
- Rate limiting (Redis-backed sliding window)
- XSS protection (input sanitization)
- Security headers (CSP, HSTS, etc.)
- Request size limits
- Bot protection

Note: CSRF protection NOT included - JWT in Authorization header prevents CSRF attacks

Configuration is loaded from environment variables via app/config.py
Copy .env.example to .env and update for your environment.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from app.config import settings
from app.routes import api_router

# Shared Core Imports - following existing project pattern
from freelancer_core.reliability.size_limit import RequestSizeLimitMiddleware
from freelancer_core.reliability.xss import XSSProtectionMiddleware
from freelancer_core.reliability.security_headers import SecurityHeadersMiddleware
from freelancer_core.reliability.bot import BotProtectionMiddleware

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
    
    # Initialize SQLite Database
    from app.repositories.database import init_db
    init_db()
    logger.info("SQLite database initialized")
    
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Rate limiting: {settings.rate_limit_requests} requests/{settings.rate_limit_window_seconds}s")
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
            {"name": "health", "description": "Health checks"},
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

    # SECURITY MIDDLEWARE (following freelancer-core pattern)
    # Each middleware in its own file, added explicitly
    # Note: CSRF protection NOT needed - JWT in Authorization header prevents CSRF
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(BotProtectionMiddleware)
    app.add_middleware(XSSProtectionMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # Include router
    app.include_router(api_router)

    # Health check
    @app.get("/healthz", tags=["health"])
    async def healthz():
        return {"status": "ok"}

    # Redis health check
    @app.get("/healthz/redis", tags=["health"])
    async def healthz_redis():
        try:
            from app.repositories.lead_repository import get_lead_repository
            repo = get_lead_repository()
            r = await repo.get_redis()
            await r.ping()
            return {"status": "ok", "redis": "connected"}
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "degraded", "redis": "disconnected", "error": str(e)}

    # Root endpoint
    @app.get("/", tags=["health"], response_class=HTMLResponse)
    async def root():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Freelancer LeadTools</title>
            <meta name="robots" content="noindex, nofollow">
        </head>
        <body>
            <h1>Freelancer LeadTools API</h1>
            <p>Free calculators for freelancers and agencies</p>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/calculators/burnout">Burnout Calculator</a></li>
                <li><a href="/calculators/rate">Rate Calculator</a></li>
                <li><a href="/calculators/agency-profit">Agency Profit Calculator</a></li>
                <li><a href="/healthz">Health Check</a></li>
            </ul>
            <p><small>Protected by rate limiting, XSS filtering, and security headers</small></p>
        </body>
        </html>
        """

    # Custom exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred",
                }
            },
            headers={
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
            }
        )

    return app


app = create_app()
