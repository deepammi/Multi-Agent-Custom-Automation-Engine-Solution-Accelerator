"""
FastAPI application entry point for MACAE LangGraph backend.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.db.mongodb import MongoDB
from app.api.v3.routes import router as v3_router
from app.api.v3.websocket import websocket_endpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    # Startup
    logger.info("🚀 Starting MACAE LangGraph backend...")
    MongoDB.connect()
    logger.info("✅ MongoDB connected")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down MACAE backend...")
    MongoDB.close()
    logger.info("👋 Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="MACAE LangGraph Backend",
    description="Multi-Agent Custom Automation Engine with LangGraph",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "macae-langgraph-backend",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MACAE LangGraph Backend API",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/api/user_browser_language")
async def user_browser_language(request: dict):
    """
    Receive user's browser language preference.
    This is called by the frontend during initialization.
    """
    language = request.get("language", "en")
    logger.info(f"User browser language: {language}")
    return {"status": "received", "language": language}


# Include API routes
app.include_router(v3_router)

# WebSocket route
app.add_api_websocket_route("/api/v3/socket/{plan_id}", websocket_endpoint)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
