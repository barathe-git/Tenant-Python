from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import owners, buildings, tenants, files, dashboard, auth
from backend.models.database import init_db
from utils.scheduler import start_scheduler, stop_scheduler
import os
import atexit

# Initialize database
init_db()

# Start scheduler
start_scheduler()

# Register cleanup function
atexit.register(stop_scheduler)

app = FastAPI(
    title="Tenant Management System API",
    description="API for managing owners, buildings, and tenants with multi-client support",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(owners.router)
app.include_router(buildings.router)
app.include_router(tenants.router)
app.include_router(files.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {
        "message": "Tenant Management System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path
    
    # Add project root to Python path if running directly
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)

