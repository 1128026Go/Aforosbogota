"""
FastAPI application for AFOROS RILSA v3.0.2 Configuration Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import analysis_router, config_router, datasets_router, reports_router

# Create FastAPI app
app = FastAPI(
    title="AFOROS RILSA Configuration API",
    description="Backend API for dataset configuration, access definition, and RILSA rule generation",
    version="3.0.2",
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3004", "127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config_router)
app.include_router(datasets_router)
app.include_router(reports_router)
app.include_router(analysis_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "3.0.2"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AFOROS RILSA Configuration API",
        "version": "3.0.2",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "datasets": "/api/v1/datasets/...",
            "config": "/api/v1/config/...",
            "reports": "/api/v1/reports/...",
            "analysis": "/api/v1/analysis/...",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3004,
        reload=True,
    )

