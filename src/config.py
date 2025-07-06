"""
Configuration settings for Structural Heart LLM System
Cost-optimized multi-model approach with caching
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass

class Settings(BaseModel):
    """Application settings with environment variable support"""
    
    # Model configurations for different complexity levels
    BASIC_MODEL_NAME: str = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
    INTERMEDIATE_MODEL_NAME: str = "microsoft/BiomedNLP-PubMedBERT-large-uncased-abstract"
    ADVANCED_MODEL_NAME: str = "microsoft/BiomedNLP-PubMedBERT-large-uncased-abstract-fulltext"
    
    # Cost optimization settings
    MAX_TOKENS_BASIC: int = 512
    MAX_TOKENS_INTERMEDIATE: int = 1024
    MAX_TOKENS_ADVANCED: int = 2048
    
    # Caching configuration
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_MAX_SIZE: int = 10000
    
    # Query complexity thresholds
    BASIC_COMPLEXITY_THRESHOLD: int = 50
    INTERMEDIATE_COMPLEXITY_THRESHOLD: int = 150
    
    # Security settings
    API_KEY_HEADER: str = "X-API-Key"
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"

@dataclass
class ModelConfig:
    """Configuration for each model tier"""
    name: str
    max_tokens: int
    cost_per_token: float
    complexity_threshold: int
    use_gpu: bool = True

class ModelRegistry:
    """Registry of available models with cost and performance characteristics"""
    
    def __init__(self):
        self.models = {
            "basic": ModelConfig(
                name="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract",
                max_tokens=512,
                cost_per_token=0.0001,  # Lower cost for basic queries
                complexity_threshold=50,
                use_gpu=False  # CPU for basic queries to save cost
            ),
            "intermediate": ModelConfig(
                name="microsoft/BiomedNLP-PubMedBERT-large-uncased-abstract",
                max_tokens=1024,
                cost_per_token=0.0005,  # Medium cost
                complexity_threshold=150,
                use_gpu=True
            ),
            "advanced": ModelConfig(
                name="microsoft/BiomedNLP-PubMedBERT-large-uncased-abstract-fulltext",
                max_tokens=2048,
                cost_per_token=0.001,  # Higher cost for complex queries
                complexity_threshold=999999,  # Large number for advanced model
                use_gpu=True
            )
        }
    
    def get_model_for_complexity(self, complexity_score: int) -> ModelConfig:
        """Select the most cost-effective model based on query complexity"""
        if complexity_score <= self.models["basic"].complexity_threshold:
            return self.models["basic"]
        elif complexity_score <= self.models["intermediate"].complexity_threshold:
            return self.models["intermediate"]
        else:
            return self.models["advanced"]
    
    def estimate_cost(self, model_name: str, token_count: int) -> float:
        """Estimate cost for a given model and token count"""
        model = self.models.get(model_name)
        if not model:
            raise ValueError(f"Unknown model: {model_name}")
        return model.cost_per_token * token_count

# Global settings instance
settings = Settings()
model_registry = ModelRegistry() 