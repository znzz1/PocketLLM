"""
PocketLLM Backend - FastAPI Application

Main entry point for the PocketLLM backend service.
Implements the architecture from HW3 with service-based design.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import configuration
from config import settings

# Import services
from auth.service import AuthService
from services.session_service import SessionService
from services.cache_service import CacheManager
from services.llm_service import LLMEngine, ModelInferenceService
from services.monitoring_service import MonitoringService

# Import routers
from routers.auth_router import router as auth_router
from routers.chat_router import router as chat_router
from routers.admin_router import router as admin_router

# Import dependencies module to set global instances
import utils.dependencies as deps


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    """
    # Startup
    print("=" * 60)
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 60)

    # Initialize services
    print("Initializing services...")

    # Auth service
    auth_service = AuthService()
    print(" Auth service initialized")

    # Session service
    session_service = SessionService()
    print(" Session service initialized")

    # Cache manager
    cache_manager = CacheManager()
    if cache_manager.enabled:
        print(f" Cache manager initialized (Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT})")
    else:
        print(" Cache manager disabled (Redis not available)")

    # LLM engine
    llm_engine = LLMEngine()
    model_loaded = llm_engine.load_model()
    if model_loaded:
        print(f" LLM engine initialized (Model: {settings.MODEL_PATH})")
    else:
        print(" LLM engine in mock mode (Model not loaded)")

    # Inference service
    inference_service = ModelInferenceService(cache_manager, llm_engine)
    print(" Inference service initialized")

    # Monitoring service
    monitoring_service = MonitoringService()
    print(" Monitoring service initialized")

    # Set global service instances for dependency injection
    deps.auth_service = auth_service
    deps.session_service = session_service
    deps.cache_manager = cache_manager
    deps.inference_service = inference_service
    deps.monitoring_service = monitoring_service

    print("=" * 60)
    print(f"Server ready on http://{settings.HOST}:{settings.PORT}")
    print(f"API docs available at http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 60)
    print("\nDefault users:")
    print("  Regular user: username='user1', password='password123'")
    print("  Admin user:   username='admin', password='admin123'")
    print("=" * 60)

    yield

    # Shutdown
    print("\nShutting down services...")
    print("Goodbye!")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="PocketLLM Backend API - Local LLM Chat Portal",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    cache_stats = deps.cache_manager.get_stats()
    model_info = deps.inference_service.llm_engine.get_model_info()

    return {
        "status": "healthy",
        "services": {
            "auth": "running",
            "cache": "running" if deps.cache_manager.enabled else "disabled",
            "llm": "running" if model_info["model_loaded"] else "mock",
        },
        "uptime_seconds": deps.monitoring_service.get_uptime()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
