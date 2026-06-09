from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from backend.core.db_init import init_db
from backend.core.limiter import limiter
from backend.core.config import verify_environment
from backend.core.logging_config import setup_logging
from backend.api.routers import auth, calculator, recommendations, challenges, analytics
from backend.middleware.errors import (
    global_exception_handler,
    database_exception_handler,
    validation_exception_handler,
)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup structured JSON logging
    setup_logging()
    
    # Run boot checks
    verify_environment()
    
    # Initialize DB tables & seed challenges
    init_db()
    yield

import os

root_path = "/api" if os.getenv("VERCEL") else ""

app = FastAPI(
    title="EcoTrack AI API",
    description="Backend services for the EcoTrack AI Carbon Footprint Awareness Platform",
    version="1.0.0",
    lifespan=lifespan,
    root_path=root_path
)

# Set rate limiter and register error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secure Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    return response

# Include API Routers
app.include_router(auth.router)
app.include_router(calculator.router)
app.include_router(recommendations.router)
app.include_router(challenges.router)
app.include_router(analytics.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to EcoTrack AI API.",
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
