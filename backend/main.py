"""
Reunite AI 1.5 - FastAPI Backend
Main application entry point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import routers
from api.routers import auth, cases, public, matching

# Import database initialization
from pages.helper.db_queries import create_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    create_db()
    yield


app = FastAPI(
    title="Reunite AI API",
    description="API for missing persons case management and face matching",
    version="1.5.0",
    lifespan=lifespan,
)

# CORS configuration - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving images
resources_path = os.path.join(os.path.dirname(__file__), "resources")
if os.path.exists(resources_path):
    app.mount("/resources", StaticFiles(directory=resources_path), name="resources")

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(cases.router, prefix="/api/v1/cases", tags=["Registered Cases"])
app.include_router(public.router, prefix="/api/v1/public", tags=["Public Submissions"])
app.include_router(matching.router, prefix="/api/v1", tags=["Matching & Statistics"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": "Reunite AI API",
        "version": "1.5.0",
    }


@app.get("/api/v1/health")
async def health_check():
    """API health check."""
    return {"status": "ok"}
