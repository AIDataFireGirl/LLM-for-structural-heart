#!/usr/bin/env python3
"""
Main entry point for Structural Heart LLM System
Cost-optimized multi-model approach with caching
"""

import uvicorn
import structlog
from src.api import app
from src.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def main():
    """Main application entry point"""
    logger.info("Starting Structural Heart LLM System")
    
    # Log configuration
    logger.info("Configuration loaded", 
                basic_model=settings.BASIC_MODEL_NAME,
                intermediate_model=settings.INTERMEDIATE_MODEL_NAME,
                advanced_model=settings.ADVANCED_MODEL_NAME)
    
    # Start the FastAPI server
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main() 