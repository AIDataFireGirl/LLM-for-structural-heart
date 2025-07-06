"""
FastAPI REST API for Structural Heart LLM System
Provides secure endpoints with rate limiting and monitoring
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import time
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY

from .llm_manager import llm_manager, LLMResponse
from .config import settings
from .cache_manager import cache_manager

# Initialize logging
logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Structural Heart LLM API",
    description="Cost-optimized LLM system for structural heart domain",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Prometheus metrics
REQUEST_COUNT = Counter('llm_requests_total', 'Total LLM requests', ['model', 'status'])
REQUEST_DURATION = Histogram('llm_request_duration_seconds', 'LLM request duration', ['model'])
CACHE_HIT_COUNT = Counter('cache_hits_total', 'Total cache hits')
CACHE_MISS_COUNT = Counter('cache_misses_total', 'Total cache misses')

# Rate limiting
request_times = {}

class QueryRequest(BaseModel):
    """Request model for LLM queries"""
    query: str = Field(..., description="The query to process", min_length=1, max_length=1000)
    force_model: Optional[str] = Field(None, description="Force specific model (basic/intermediate/advanced)")
    include_analysis: bool = Field(False, description="Include query analysis in response")

class QueryResponse(BaseModel):
    """Response model for LLM queries"""
    response: str
    model_used: str
    cost: float
    processing_time: float
    cache_hit: bool
    complexity_score: int
    confidence: float
    analysis: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    models_loaded: int
    cache_healthy: bool
    uptime: float

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify API key for authentication"""
    # In production, validate against database or environment variable
    expected_key = "your-api-key-here"  # Replace with secure key management
    return credentials.credentials == expected_key

def check_rate_limit(request: Request):
    """Check rate limiting for requests"""
    client_ip = request.client.host
    current_time = time.time()
    
    if client_ip in request_times:
        # Remove old requests (older than 1 minute)
        request_times[client_ip] = [t for t in request_times[client_ip] if current_time - t < 60]
        
        # Check if rate limit exceeded
        if len(request_times[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
    
    # Add current request
    if client_ip not in request_times:
        request_times[client_ip] = []
    request_times[client_ip].append(current_time)

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Structural Heart LLM API",
        "version": "1.0.0",
        "description": "Cost-optimized LLM system for structural heart domain"
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """Process a query with optimal model selection and caching"""
    # Check rate limiting
    check_rate_limit(request)
    
    start_time = time.time()
    
    try:
        # Process query
        llm_response = llm_manager.process_query(
            query=request.query,
            force_model=request.force_model
        )
        
        # Update metrics
        REQUEST_COUNT.labels(model=llm_response.model_used, status="success").inc()
        REQUEST_DURATION.labels(model=llm_response.model_used).observe(llm_response.processing_time)
        
        if llm_response.cache_hit:
            CACHE_HIT_COUNT.inc()
        else:
            CACHE_MISS_COUNT.inc()
        
        # Prepare response
        response_data = {
            "response": llm_response.response,
            "model_used": llm_response.model_used,
            "cost": llm_response.cost,
            "processing_time": llm_response.processing_time,
            "cache_hit": llm_response.cache_hit,
            "complexity_score": llm_response.complexity_score,
            "confidence": llm_response.confidence
        }
        
        # Include analysis if requested
        if request.include_analysis:
            cost_analysis = llm_manager.estimate_cost_for_query(request.query)
            response_data["analysis"] = cost_analysis
        
        logger.info(f"Query processed successfully: {request.query[:50]}...")
        return QueryResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        REQUEST_COUNT.labels(model="unknown", status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    start_time = time.time()
    
    # Check system health
    models_loaded = len(llm_manager.models)
    cache_healthy = cache_manager.is_cache_healthy()
    
    # Determine overall status
    status = "healthy" if models_loaded > 0 and cache_healthy else "unhealthy"
    
    return HealthResponse(
        status=status,
        models_loaded=models_loaded,
        cache_healthy=cache_healthy,
        uptime=time.time() - start_time
    )

@app.get("/models/status")
async def get_model_status():
    """Get status of all models"""
    return llm_manager.get_model_status()

@app.get("/models/cost-estimate")
async def estimate_cost(query: str):
    """Estimate cost for processing a query with different models"""
    return llm_manager.estimate_cost_for_query(query)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return JSONResponse(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    return cache_manager.get_cache_stats()

@app.delete("/cache/clear")
async def clear_cache(cache_type: str = "all"):
    """Clear cache"""
    cache_manager.clear_cache(cache_type)
    return {"message": f"Cache cleared: {cache_type}"}

@app.get("/performance")
async def get_performance_metrics():
    """Get performance metrics"""
    return llm_manager.get_performance_metrics()

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Structural Heart LLM API")
    
    # Initialize components
    try:
        # Check if models are loaded
        if len(llm_manager.models) == 0:
            logger.warning("No models loaded")
        
        # Check cache health
        if not cache_manager.is_cache_healthy():
            logger.warning("Cache system unhealthy")
        
        logger.info("API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Structural Heart LLM API")
    
    # Clear rate limiting data
    request_times.clear()
    
    logger.info("API shutdown completed") 