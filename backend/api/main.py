"""FastAPI application factory."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import prices_router, inventory_router, pos_router, agent_router
import logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Price Optimizer API",
        description="ML-Powered Dynamic Price Optimization Engine",
        version="0.1.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(prices_router)
    app.include_router(inventory_router)
    app.include_router(pos_router)
    app.include_router(agent_router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Price Optimizer API"}

    return app
