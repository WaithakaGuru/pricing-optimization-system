"""Main application entry point."""
import logging
import asyncio
from backend.api.main import create_app
from utils.logger import setup_logging
from utils.config import settings

# Setup logging
logger = setup_logging()


async def main():
    """Start the application."""
    logger.info(f"Starting Price Optimizer API on {settings.api_host}:{settings.api_port}")
    logger.info(f"RL Training: {'Enabled' if settings.rl_enabled else 'Disabled'}")
    
    # Create FastAPI app
    app = create_app()
    
    # TODO: In production, run with: uvicorn main:app --host 0.0.0.0 --port 8000
    # For development, you can use:
    # import uvicorn
    # uvicorn.run(app, host=settings.api_host, port=settings.api_port)
    
    return app


if __name__ == "__main__":
    # For local development - requires uvicorn
    import uvicorn
    app = asyncio.run(main())
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, reload=settings.api_debug)
