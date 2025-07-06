"""
Cache Manager for Structural Heart LLM System
Implements Redis-based caching with cost optimization
"""

import hashlib
import json
import pickle
from typing import Optional, Any, Dict
import redis
from cachetools import TTLCache, LRUCache
import structlog
from .config import settings

logger = structlog.get_logger()

class CacheManager:
    """Manages caching for LLM queries to optimize costs and performance"""
    
    def __init__(self):
        """Initialize cache manager with Redis and in-memory caches"""
        # Redis for persistent caching
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.redis_available = True
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache only: {e}")
            self.redis_available = False
        
        # In-memory cache for frequently accessed items
        self.memory_cache = TTLCache(
            maxsize=settings.CACHE_MAX_SIZE,
            ttl=settings.CACHE_TTL
        )
        
        # LRU cache for model responses
        self.response_cache = LRUCache(maxsize=1000)
    
    def _generate_cache_key(self, query: str, model_name: str, **kwargs) -> str:
        """Generate a unique cache key for the query and model combination"""
        # Create a hash of the query and parameters
        cache_data = {
            "query": query,
            "model": model_name,
            "params": kwargs
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    def get_cached_response(self, query: str, model_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Retrieve cached response if available"""
        cache_key = self._generate_cache_key(query, model_name, **kwargs)
        
        # Check in-memory cache first (faster)
        if cache_key in self.memory_cache:
            logger.debug(f"Cache hit in memory for key: {cache_key[:8]}")
            return self.memory_cache[cache_key]
        
        # Check Redis cache
        if self.redis_available:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    response = pickle.loads(cached_data)
                    # Store in memory cache for faster future access
                    self.memory_cache[cache_key] = response
                    logger.debug(f"Cache hit in Redis for key: {cache_key[:8]}")
                    return response
            except Exception as e:
                logger.error(f"Error retrieving from Redis cache: {e}")
        
        logger.debug(f"Cache miss for key: {cache_key[:8]}")
        return None
    
    def cache_response(self, query: str, model_name: str, response: Dict[str, Any], **kwargs) -> None:
        """Cache the response for future use"""
        cache_key = self._generate_cache_key(query, model_name, **kwargs)
        
        # Store in memory cache
        self.memory_cache[cache_key] = response
        
        # Store in Redis for persistence
        if self.redis_available:
            try:
                serialized_response = pickle.dumps(response)
                self.redis_client.setex(
                    cache_key,
                    settings.CACHE_TTL,
                    serialized_response
                )
                logger.debug(f"Cached response with key: {cache_key[:8]}")
            except Exception as e:
                logger.error(f"Error caching in Redis: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        stats = {
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_maxsize": self.memory_cache.maxsize,
            "response_cache_size": len(self.response_cache),
            "redis_available": self.redis_available
        }
        
        if self.redis_available:
            try:
                stats["redis_info"] = self.redis_client.info()
            except Exception as e:
                logger.error(f"Error getting Redis info: {e}")
                stats["redis_info"] = None
        
        return stats
    
    def clear_cache(self, cache_type: str = "all") -> None:
        """Clear specified cache type"""
        if cache_type in ["all", "memory"]:
            self.memory_cache.clear()
            logger.info("Memory cache cleared")
        
        if cache_type in ["all", "redis"] and self.redis_available:
            try:
                self.redis_client.flushdb()
                logger.info("Redis cache cleared")
            except Exception as e:
                logger.error(f"Error clearing Redis cache: {e}")
    
    def is_cache_healthy(self) -> bool:
        """Check if cache system is healthy"""
        try:
            # Test memory cache
            test_key = "health_check"
            self.memory_cache[test_key] = "test"
            del self.memory_cache[test_key]
            
            # Test Redis if available
            if self.redis_available:
                self.redis_client.ping()
            
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False

# Global cache manager instance
cache_manager = CacheManager() 