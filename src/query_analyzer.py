"""
Query Analyzer for Structural Heart LLM System
Analyzes query complexity to optimize model selection and costs
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from transformers import AutoTokenizer
import structlog

logger = structlog.get_logger()

@dataclass
class QueryAnalysis:
    """Results of query complexity analysis"""
    complexity_score: int
    query_type: str
    medical_terms: List[str]
    structural_heart_terms: List[str]
    recommended_model: str
    estimated_cost: float
    confidence: float

class QueryAnalyzer:
    """Analyzes queries to determine complexity and optimal model selection"""
    
    def __init__(self):
        """Initialize the query analyzer with medical terminology"""
        # Structural heart specific terminology
        self.structural_heart_terms = {
            "aortic valve", "mitral valve", "tricuspid valve", "pulmonary valve",
            "valvular stenosis", "valvular regurgitation", "prolapse",
            "annuloplasty", "valve replacement", "transcatheter",
            "echocardiography", "cardiac catheterization", "cardiac MRI",
            "left ventricular", "right ventricular", "atrial", "ventricular",
            "ejection fraction", "cardiac output", "stroke volume",
            "coronary artery", "myocardial infarction", "cardiomyopathy",
            "congenital heart disease", "rheumatic heart disease"
        }
        
        # Medical terminology patterns
        self.medical_patterns = [
            r'\b\d+\.?\d*\s*(mm|cm|ml|mmHg|bpm|%)\b',  # Measurements
            r'\b(grade|severity|mild|moderate|severe)\b',  # Severity terms
            r'\b(procedure|surgery|intervention|treatment)\b',  # Medical procedures
            r'\b(diagnosis|diagnostic|assessment|evaluation)\b',  # Diagnostic terms
            r'\b(patient|case|history|symptoms)\b',  # Clinical terms
        ]
        
        # Complexity scoring weights
        self.complexity_weights = {
            "structural_heart_terms": 10,
            "medical_measurements": 5,
            "medical_procedures": 8,
            "diagnostic_terms": 6,
            "clinical_terms": 4,
            "query_length": 0.1,
            "technical_terms": 3
        }
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze query complexity and recommend optimal model"""
        # Normalize query
        normalized_query = query.lower().strip()
        
        # Extract features
        structural_terms = self._extract_structural_heart_terms(normalized_query)
        medical_measurements = self._extract_medical_measurements(normalized_query)
        medical_procedures = self._extract_medical_procedures(normalized_query)
        diagnostic_terms = self._extract_diagnostic_terms(normalized_query)
        clinical_terms = self._extract_clinical_terms(normalized_query)
        technical_terms = self._extract_technical_terms(normalized_query)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(
            normalized_query,
            structural_terms,
            medical_measurements,
            medical_procedures,
            diagnostic_terms,
            clinical_terms,
            technical_terms
        )
        
        # Determine query type
        query_type = self._determine_query_type(normalized_query, structural_terms)
        
        # Recommend model based on complexity
        recommended_model = self._recommend_model(complexity_score)
        
        # Estimate cost
        estimated_cost = self._estimate_cost(complexity_score, len(normalized_query.split()))
        
        # Calculate confidence
        confidence = self._calculate_confidence(complexity_score, structural_terms)
        
        return QueryAnalysis(
            complexity_score=complexity_score,
            query_type=query_type,
            medical_terms=structural_terms + medical_measurements + medical_procedures,
            structural_heart_terms=structural_terms,
            recommended_model=recommended_model,
            estimated_cost=estimated_cost,
            confidence=confidence
        )
    
    def _extract_structural_heart_terms(self, query: str) -> List[str]:
        """Extract structural heart specific terminology"""
        found_terms = []
        for term in self.structural_heart_terms:
            if term in query:
                found_terms.append(term)
        return found_terms
    
    def _extract_medical_measurements(self, query: str) -> List[str]:
        """Extract medical measurements and values"""
        measurements = re.findall(r'\b\d+\.?\d*\s*(mm|cm|ml|mmHg|bpm|%)\b', query)
        return measurements
    
    def _extract_medical_procedures(self, query: str) -> List[str]:
        """Extract medical procedure terms"""
        procedure_pattern = r'\b(procedure|surgery|intervention|treatment|operation)\b'
        procedures = re.findall(procedure_pattern, query)
        return procedures
    
    def _extract_diagnostic_terms(self, query: str) -> List[str]:
        """Extract diagnostic and assessment terms"""
        diagnostic_pattern = r'\b(diagnosis|diagnostic|assessment|evaluation|examination)\b'
        diagnostics = re.findall(diagnostic_pattern, query)
        return diagnostics
    
    def _extract_clinical_terms(self, query: str) -> List[str]:
        """Extract clinical terminology"""
        clinical_pattern = r'\b(patient|case|history|symptoms|clinical)\b'
        clinical = re.findall(clinical_pattern, query)
        return clinical
    
    def _extract_technical_terms(self, query: str) -> List[str]:
        """Extract technical and scientific terms"""
        technical_pattern = r'\b(algorithm|protocol|methodology|analysis|computation)\b'
        technical = re.findall(technical_pattern, query)
        return technical
    
    def _calculate_complexity_score(self, query: str, structural_terms: List[str],
                                  medical_measurements: List[str], medical_procedures: List[str],
                                  diagnostic_terms: List[str], clinical_terms: List[str],
                                  technical_terms: List[str]) -> int:
        """Calculate overall complexity score"""
        score = 0
        
        # Base score from query length
        score += len(query.split()) * self.complexity_weights["query_length"]
        
        # Add scores for different term types
        score += len(structural_terms) * self.complexity_weights["structural_heart_terms"]
        score += len(medical_measurements) * self.complexity_weights["medical_measurements"]
        score += len(medical_procedures) * self.complexity_weights["medical_procedures"]
        score += len(diagnostic_terms) * self.complexity_weights["diagnostic_terms"]
        score += len(clinical_terms) * self.complexity_weights["clinical_terms"]
        score += len(technical_terms) * self.complexity_weights["technical_terms"]
        
        return int(score)
    
    def _determine_query_type(self, query: str, structural_terms: List[str]) -> str:
        """Determine the type of query"""
        if "diagnosis" in query or "diagnostic" in query:
            return "diagnostic"
        elif "treatment" in query or "procedure" in query or "surgery" in query:
            return "therapeutic"
        elif "measurement" in query or "assessment" in query:
            return "assessment"
        elif structural_terms:
            return "structural_heart_specific"
        else:
            return "general"
    
    def _recommend_model(self, complexity_score: int) -> str:
        """Recommend the most cost-effective model based on complexity"""
        if complexity_score <= 50:
            return "basic"
        elif complexity_score <= 150:
            return "intermediate"
        else:
            return "advanced"
    
    def _estimate_cost(self, complexity_score: int, token_count: int) -> float:
        """Estimate the cost of processing the query"""
        # Base cost estimation
        base_cost = 0.001
        
        # Adjust based on complexity
        if complexity_score > 150:
            cost_multiplier = 2.0
        elif complexity_score > 50:
            cost_multiplier = 1.5
        else:
            cost_multiplier = 1.0
        
        return base_cost * cost_multiplier * (token_count / 100)
    
    def _calculate_confidence(self, complexity_score: int, structural_terms: List[str]) -> float:
        """Calculate confidence in the analysis"""
        # Higher confidence for queries with structural heart terms
        base_confidence = 0.7
        
        if structural_terms:
            base_confidence += 0.2
        
        # Adjust based on complexity score
        if 20 <= complexity_score <= 200:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)

# Global query analyzer instance
query_analyzer = QueryAnalyzer() 