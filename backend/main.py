"""
FastAPI Main Application
File: backend/main.py
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time
import asyncio

from backend.config.settings import settings, validate_settings
from backend.config.database import check_db_connection
from backend.api.routes import auth, users

# Setup logging first
from backend.utils.logger import setup_logging
setup_logging()


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Enabled Smart Procurement System for Ayurvedic Clinics",
    docs_url=f"/api/{settings.API_VERSION}/docs",
    redoc_url=f"/api/{settings.API_VERSION}/redoc",
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json"
)


# ============================================
# MIDDLEWARE CONFIGURATION
# ============================================

# CORS Middleware — allow all origins for demo deployment.
# Auth uses Bearer tokens in headers (not cookies), so credentials=False is safe.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} | Time: {process_time:.3f}s | Path: {request.url.path}")
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ============================================
# EXCEPTION HANDLERS
# ============================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "message": str(exc) if settings.DEBUG else "An error occurred"}
    )


# ============================================
# STARTUP & SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    logger.info("="*70)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("="*70)

    try:
        validate_settings()
        logger.info("✓ Settings validated successfully")
    except Exception as e:
        logger.error(f"✗ Settings validation failed: {e}")
        raise

    # Check DB with a timeout — Neon free tier scales to zero and can take
    # 15-60s to cold-start. Without a timeout this blocks the startup event,
    # which prevents uvicorn from accepting Render's health-check request,
    # causing the deploy to time out and fail.
    try:
        db_ok = await asyncio.wait_for(
            asyncio.to_thread(check_db_connection),
            timeout=15.0
        )
        if db_ok:
            logger.info("✓ Database connection successful")
        else:
            logger.warning("⚠ DB check returned false — will connect on first request")
    except asyncio.TimeoutError:
        logger.warning("⚠ DB connection timed out (Neon cold-start?) — server starting anyway")

    logger.info(f"✓ Server running in {settings.ENVIRONMENT} mode")
    logger.info(f"✓ API Documentation: http://{settings.HOST}:{settings.PORT}/api/{settings.API_VERSION}/docs")
    logger.info("="*70)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("="*70)
    logger.info("Shutting down application...")
    logger.info("="*70)


# ============================================
# ROOT ROUTES
# ============================================

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"/api/{settings.API_VERSION}/docs"
    }


@app.get("/health")
async def health_check():
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# ============================================
# API ROUTES
# ============================================

# Include routers with API version prefix
api_prefix = f"/api/{settings.API_VERSION}"

# Import all route modules
from backend.api.routes import (
    auth, users, patients, medicines, inventory, 
    vendors, procurement, appointments, billing, reports, chatbot
)

# Include all routers
app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(patients.router, prefix=api_prefix)
app.include_router(medicines.router, prefix=api_prefix)
app.include_router(inventory.router, prefix=api_prefix)
app.include_router(vendors.router, prefix=api_prefix)
app.include_router(procurement.router, prefix=api_prefix)
app.include_router(appointments.router, prefix=api_prefix)
app.include_router(billing.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)
app.include_router(chatbot.router, prefix=api_prefix)

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == "__main__":
    import uvicorn

    # Note: use full module path "backend.main:app" when running from project root
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
