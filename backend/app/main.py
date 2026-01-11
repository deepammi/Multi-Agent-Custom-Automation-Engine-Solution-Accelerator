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
    
    # Connect to MongoDB
    MongoDB.connect()
    logger.info("✅ MongoDB connected")
    
    # Initialize validation rules configuration
    logger.info("📋 Loading validation rules configuration...")
    from app.config.validation_rules import ValidationRulesConfig
    import os
    
    # Load from environment variables
    ValidationRulesConfig.load_from_env()
    
    # Load from config file if exists
    config_file = os.getenv("VALIDATION_RULES_CONFIG", "validation_rules.json")
    if os.path.exists(config_file):
        ValidationRulesConfig.load_from_config_file(config_file)
        logger.info(f"✅ Loaded validation rules from {config_file}")
    
    # Log enabled rules
    enabled_rules = ValidationRulesConfig.get_enabled_rules()
    logger.info(f"✅ Validation rules loaded: {len(enabled_rules)} enabled")
    for rule in enabled_rules:
        logger.info(f"   - {rule.name} ({rule.severity})")
    
    # Initialize LangExtract service if extraction is enabled
    enable_extraction = os.getenv("ENABLE_STRUCTURED_EXTRACTION", "false").lower() == "true"
    if enable_extraction:
        logger.info("📊 Initializing LangExtract service...")
        from app.services.langextract_service import LangExtractService
        
        try:
            LangExtractService.initialize()
            logger.info("✅ LangExtract service initialized")
        except Exception as e:
            logger.warning(f"⚠️  LangExtract initialization failed: {e}")
            logger.warning("   Extraction features will be disabled")
    else:
        logger.info("📊 Structured extraction disabled (ENABLE_STRUCTURED_EXTRACTION=false)")
    
    # Log configuration summary
    logger.info("\n" + "="*60)
    logger.info("CONFIGURATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"MongoDB: {os.getenv('MONGODB_URL', 'mongodb://localhost:27017')}")
    logger.info(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'openai')}")
    logger.info(f"Mock LLM: {os.getenv('USE_MOCK_LLM', 'false')}")
    logger.info(f"Structured Extraction: {enable_extraction}")
    if enable_extraction:
        logger.info(f"Gemini Model: {os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')}")
        logger.info(f"Extraction Validation: {os.getenv('EXTRACTION_VALIDATION', 'true')}")
        logger.info(f"Requires Approval: {os.getenv('EXTRACTION_REQUIRES_APPROVAL', 'true')}")
    logger.info("="*60 + "\n")
    
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
app.websocket("/api/v3/socket/{plan_id}")(websocket_endpoint)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
