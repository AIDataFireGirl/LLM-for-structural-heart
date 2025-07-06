"""
Test suite for Structural Heart LLM System
Tests query analysis, caching, and model management
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.query_analyzer import QueryAnalyzer, QueryAnalysis
from src.cache_manager import CacheManager
from src.llm_manager import LLMManager, LLMResponse
from src.config import model_registry

class TestQueryAnalyzer:
    """Test cases for query analysis functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = QueryAnalyzer()
    
    def test_basic_query_analysis(self):
        """Test analysis of a basic query"""
        query = "What is aortic valve stenosis?"
        analysis = self.analyzer.analyze_query(query)
        
        assert isinstance(analysis, QueryAnalysis)
        assert analysis.complexity_score > 0
        assert "aortic valve" in analysis.structural_heart_terms
        assert analysis.recommended_model in ["basic", "intermediate", "advanced"]
        assert 0 <= analysis.confidence <= 1
    
    def test_complex_query_analysis(self):
        """Test analysis of a complex medical query"""
        query = "Patient with severe aortic valve stenosis measuring 2.5 cm with ejection fraction 35% requires surgical intervention"
        analysis = self.analyzer.analyze_query(query)
        
        assert analysis.complexity_score > 50  # Should be higher than basic
        assert len(analysis.medical_terms) > 0
        assert analysis.query_type in ["diagnostic", "therapeutic", "assessment"]
    
    def test_medical_measurements_extraction(self):
        """Test extraction of medical measurements"""
        query = "Ejection fraction 45%, aortic valve area 0.8 cm²"
        analysis = self.analyzer.analyze_query(query)
        
        # Should find medical measurements
        assert analysis.complexity_score > 0
    
    def test_model_recommendation(self):
        """Test model recommendation based on complexity"""
        # Basic query
        basic_query = "What is the heart?"
        basic_analysis = self.analyzer.analyze_query(basic_query)
        assert basic_analysis.recommended_model == "basic"
        
        # Complex query
        complex_query = "Complex structural heart disease with multiple valve involvement requiring comprehensive diagnostic evaluation"
        complex_analysis = self.analyzer.analyze_query(complex_query)
        assert complex_analysis.recommended_model in ["intermediate", "advanced"]

class TestCacheManager:
    """Test cases for caching functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cache_manager = CacheManager()
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        query = "Test query"
        model_name = "basic"
        
        key1 = self.cache_manager._generate_cache_key(query, model_name)
        key2 = self.cache_manager._generate_cache_key(query, model_name)
        
        assert key1 == key2  # Same inputs should generate same key
        
        # Different inputs should generate different keys
        key3 = self.cache_manager._generate_cache_key("Different query", model_name)
        assert key1 != key3
    
    def test_cache_storage_and_retrieval(self):
        """Test storing and retrieving from cache"""
        query = "Test query for caching"
        model_name = "basic"
        response_data = {"response": "Test response", "cost": 0.001}
        
        # Store in cache
        self.cache_manager.cache_response(query, model_name, response_data)
        
        # Retrieve from cache
        cached_response = self.cache_manager.get_cached_response(query, model_name)
        
        assert cached_response is not None
        assert cached_response["response"] == "Test response"
        assert cached_response["cost"] == 0.001
    
    def test_cache_miss(self):
        """Test cache miss scenario"""
        query = "Query not in cache"
        model_name = "basic"
        
        cached_response = self.cache_manager.get_cached_response(query, model_name)
        assert cached_response is None
    
    def test_cache_stats(self):
        """Test cache statistics"""
        stats = self.cache_manager.get_cache_stats()
        
        assert "memory_cache_size" in stats
        assert "redis_available" in stats
        assert isinstance(stats["memory_cache_size"], int)

class TestLLMManager:
    """Test cases for LLM management functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock the models to avoid loading actual models in tests
        self.llm_manager = LLMManager()
        self.llm_manager.models = {
            "basic": Mock(),
            "intermediate": Mock(),
            "advanced": Mock()
        }
        self.llm_manager.tokenizers = {
            "basic": Mock(),
            "intermediate": Mock(),
            "advanced": Mock()
        }
    
    @patch('src.llm_manager.query_analyzer')
    @patch('src.llm_manager.cache_manager')
    def test_process_query_with_cache_hit(self, mock_cache_manager, mock_query_analyzer):
        """Test processing query with cache hit"""
        # Mock cache hit
        mock_cache_manager.get_cached_response.return_value = {
            "response": "Cached response",
            "cost": 0.001
        }
        
        # Mock query analysis
        mock_analysis = Mock()
        mock_analysis.complexity_score = 30
        mock_analysis.recommended_model = "basic"
        mock_analysis.confidence = 0.8
        mock_query_analyzer.analyze_query.return_value = mock_analysis
        
        response = self.llm_manager.process_query("Test query")
        
        assert response.cache_hit is True
        assert response.response == "Cached response"
        assert response.model_used == "basic"
    
    @patch('src.llm_manager.query_analyzer')
    @patch('src.llm_manager.cache_manager')
    def test_process_query_with_cache_miss(self, mock_cache_manager, mock_query_analyzer):
        """Test processing query with cache miss"""
        # Mock cache miss
        mock_cache_manager.get_cached_response.return_value = None
        
        # Mock query analysis
        mock_analysis = Mock()
        mock_analysis.complexity_score = 30
        mock_analysis.recommended_model = "basic"
        mock_analysis.confidence = 0.8
        mock_query_analyzer.analyze_query.return_value = mock_analysis
        
        # Mock model processing
        with patch.object(self.llm_manager, '_process_with_model') as mock_process:
            mock_process.return_value = "Generated response"
            
            response = self.llm_manager.process_query("Test query")
            
            assert response.cache_hit is False
            assert response.response == "Generated response"
            assert response.model_used == "basic"
    
    def test_model_status(self):
        """Test getting model status"""
        status = self.llm_manager.get_model_status()
        
        assert "basic" in status
        assert "intermediate" in status
        assert "advanced" in status
        
        for model_name, model_info in status.items():
            assert "loaded" in model_info
            assert "parameters" in model_info
    
    @patch('src.llm_manager.query_analyzer')
    def test_cost_estimation(self, mock_query_analyzer):
        """Test cost estimation for queries"""
        # Mock query analysis
        mock_analysis = Mock()
        mock_analysis.complexity_score = 50
        mock_analysis.recommended_model = "intermediate"
        mock_query_analyzer.analyze_query.return_value = mock_analysis
        
        cost_estimate = self.llm_manager.estimate_cost_for_query("Test query")
        
        assert "query_analysis" in cost_estimate
        assert "model_costs" in cost_estimate
        assert "recommended_model" in cost_estimate

class TestModelRegistry:
    """Test cases for model registry functionality"""
    
    def test_model_selection_by_complexity(self):
        """Test model selection based on complexity score"""
        # Basic complexity
        basic_model = model_registry.get_model_for_complexity(30)
        assert basic_model.name == model_registry.models["basic"].name
        
        # Intermediate complexity
        intermediate_model = model_registry.get_model_for_complexity(100)
        assert intermediate_model.name == model_registry.models["intermediate"].name
        
        # Advanced complexity
        advanced_model = model_registry.get_model_for_complexity(200)
        assert advanced_model.name == model_registry.models["advanced"].name
    
    def test_cost_estimation(self):
        """Test cost estimation for different models"""
        token_count = 100
        
        basic_cost = model_registry.estimate_cost("basic", token_count)
        intermediate_cost = model_registry.estimate_cost("intermediate", token_count)
        advanced_cost = model_registry.estimate_cost("advanced", token_count)
        
        # Advanced model should be more expensive than basic
        assert advanced_cost > basic_cost
        assert intermediate_cost > basic_cost

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.integration
    def test_end_to_end_query_processing(self):
        """Test complete query processing pipeline"""
        # This would require actual model loading
        # Marked as integration test to skip in unit test runs
        pass
    
    @pytest.mark.integration
    def test_cache_integration(self):
        """Test cache integration with query processing"""
        # This would require actual cache setup
        # Marked as integration test to skip in unit test runs
        pass

if __name__ == "__main__":
    pytest.main([__file__]) 