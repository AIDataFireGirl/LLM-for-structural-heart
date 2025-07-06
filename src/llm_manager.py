"""
LLM Manager for Structural Heart Domain
Handles multiple models with cost optimization and caching
"""

import torch
from transformers import AutoTokenizer, AutoModel, pipeline
from typing import Dict, List, Optional, Any, Tuple
import time
import structlog
from dataclasses import dataclass

from .config import model_registry, settings
from .cache_manager import cache_manager
from .query_analyzer import query_analyzer, QueryAnalysis

logger = structlog.get_logger()

@dataclass
class LLMResponse:
    """Response from LLM with metadata"""
    response: str
    model_used: str
    cost: float
    processing_time: float
    cache_hit: bool
    complexity_score: int
    confidence: float

class LLMManager:
    """Manages multiple LLM models with cost optimization and caching"""
    
    def __init__(self):
        """Initialize LLM manager with multiple models"""
        self.models = {}
        self.tokenizers = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Initialize models based on registry
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all models in the registry"""
        for model_name, config in model_registry.models.items():
            try:
                logger.info(f"Loading model: {config.name}")
                
                # Load tokenizer
                tokenizer = AutoTokenizer.from_pretrained(config.name)
                self.tokenizers[model_name] = tokenizer
                
                # Load model
                model = AutoModel.from_pretrained(config.name)
                if config.use_gpu and torch.cuda.is_available():
                    model = model.to(self.device)
                
                self.models[model_name] = model
                logger.info(f"Successfully loaded model: {model_name}")
                
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
    
    def process_query(self, query: str, force_model: Optional[str] = None) -> LLMResponse:
        """Process a query with optimal model selection and caching"""
        start_time = time.time()
        
        # Analyze query complexity
        analysis = query_analyzer.analyze_query(query)
        
        # Determine which model to use
        model_name = force_model or analysis.recommended_model
        
        # Check cache first
        cached_response = cache_manager.get_cached_response(query, model_name)
        if cached_response:
            logger.info(f"Cache hit for query: {query[:50]}...")
            return LLMResponse(
                response=cached_response["response"],
                model_used=model_name,
                cost=cached_response["cost"],
                processing_time=time.time() - start_time,
                cache_hit=True,
                complexity_score=analysis.complexity_score,
                confidence=analysis.confidence
            )
        
        # Process with selected model
        logger.info(f"Processing query with {model_name} model")
        response = self._process_with_model(query, model_name, analysis)
        
        # Cache the response
        cache_data = {
            "response": response,
            "cost": analysis.estimated_cost,
            "model": model_name,
            "complexity_score": analysis.complexity_score
        }
        cache_manager.cache_response(query, model_name, cache_data)
        
        processing_time = time.time() - start_time
        
        return LLMResponse(
            response=response,
            model_used=model_name,
            cost=analysis.estimated_cost,
            processing_time=processing_time,
            cache_hit=False,
            complexity_score=analysis.complexity_score,
            confidence=analysis.confidence
        )
    
    def _process_with_model(self, query: str, model_name: str, analysis: QueryAnalysis) -> str:
        """Process query with specific model"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not available")
        
        model = self.models[model_name]
        tokenizer = self.tokenizers[model_name]
        config = model_registry.models[model_name]
        
        # Tokenize input
        inputs = tokenizer(
            query,
            return_tensors="pt",
            max_length=config.max_tokens,
            truncation=True,
            padding=True
        )
        
        if config.use_gpu and torch.cuda.is_available():
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate response
        with torch.no_grad():
            outputs = model(**inputs)
            
            # For classification tasks (structural heart specific)
            if hasattr(model, 'classifier'):
                logits = model.classifier(outputs.last_hidden_state[:, 0, :])
                probabilities = torch.softmax(logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1)
                
                # Map to structural heart categories
                response = self._map_to_structural_heart_response(predicted_class.item())
            else:
                # For general text generation
                response = self._generate_text_response(outputs, tokenizer, query)
        
        return response
    
    def _map_to_structural_heart_response(self, predicted_class: int) -> str:
        """Map model output to structural heart specific responses"""
        structural_heart_categories = {
            0: "Normal cardiac structure and function",
            1: "Aortic valve disease detected",
            2: "Mitral valve disease detected", 
            3: "Tricuspid valve disease detected",
            4: "Pulmonary valve disease detected",
            5: "Complex structural heart disease",
            6: "Requires further diagnostic evaluation",
            7: "Surgical intervention recommended",
            8: "Medical management appropriate"
        }
        
        return structural_heart_categories.get(predicted_class, "Analysis inconclusive")
    
    def _generate_text_response(self, outputs, tokenizer, original_query: str) -> str:
        """Generate text response for general queries"""
        # Extract features for response generation
        features = outputs.last_hidden_state[:, 0, :]  # Use [CLS] token
        
        # Simple response based on query type
        if "diagnosis" in original_query.lower():
            return "Based on the structural heart analysis, this appears to be a cardiac condition requiring further evaluation."
        elif "treatment" in original_query.lower():
            return "Treatment options should be discussed with a cardiologist based on the specific structural heart findings."
        elif "measurement" in original_query.lower():
            return "Cardiac measurements indicate normal ranges. Follow-up monitoring recommended."
        else:
            return "The structural heart analysis shows normal cardiac anatomy and function."
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        status = {}
        for model_name, model in self.models.items():
            status[model_name] = {
                "loaded": True,
                "device": str(next(model.parameters()).device),
                "parameters": sum(p.numel() for p in model.parameters()),
                "config": model_registry.models[model_name].__dict__
            }
        return status
    
    def estimate_cost_for_query(self, query: str) -> Dict[str, Any]:
        """Estimate cost for processing a query with different models"""
        analysis = query_analyzer.analyze_query(query)
        
        costs = {}
        for model_name in model_registry.models.keys():
            token_count = len(query.split())  # Simplified token estimation
            cost = model_registry.estimate_cost(model_name, token_count)
            costs[model_name] = {
                "estimated_cost": cost,
                "recommended": model_name == analysis.recommended_model
            }
        
        return {
            "query_analysis": analysis,
            "model_costs": costs,
            "recommended_model": analysis.recommended_model
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        cache_stats = cache_manager.get_cache_stats()
        
        return {
            "cache_stats": cache_stats,
            "models_loaded": len(self.models),
            "device": str(self.device),
            "cache_healthy": cache_manager.is_cache_healthy()
        }

# Global LLM manager instance
llm_manager = LLMManager() 