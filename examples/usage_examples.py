"""
Usage Examples for Structural Heart LLM System
Demonstrates cost-optimized multi-model approach with caching
"""

import asyncio
import json
from typing import Dict, Any

# Example queries for different complexity levels
EXAMPLE_QUERIES = {
    "basic": [
        "What is the heart?",
        "Explain aortic valve",
        "What is mitral valve disease?",
        "Basic heart anatomy",
        "Simple cardiac function"
    ],
    "intermediate": [
        "Patient with moderate aortic valve stenosis measuring 1.2 cm²",
        "Ejection fraction 45% with mild mitral regurgitation",
        "Cardiac catheterization shows coronary artery disease",
        "Echocardiogram reveals tricuspid valve prolapse",
        "Structural heart assessment for surgical planning"
    ],
    "advanced": [
        "Complex structural heart disease with multiple valve involvement: severe aortic stenosis (0.8 cm²), moderate mitral regurgitation, and mild tricuspid regurgitation. Patient has ejection fraction 35% and requires comprehensive diagnostic evaluation for surgical intervention.",
        "Multi-valvular heart disease assessment: Patient presents with severe aortic valve stenosis (peak gradient 80 mmHg, mean gradient 45 mmHg), moderate-to-severe mitral regurgitation (vena contracta 0.6 cm), and mild tricuspid regurgitation. Cardiac MRI shows left ventricular ejection fraction 30% with evidence of myocardial fibrosis. Requires detailed evaluation for combined valve surgery vs. transcatheter interventions.",
        "Advanced structural heart imaging analysis: 3D echocardiography demonstrates complex bicuspid aortic valve with severe stenosis (AVA 0.7 cm², peak velocity 4.2 m/s) and associated ascending aortic aneurysm (5.2 cm). Cardiac CT confirms coronary anatomy and rules out significant CAD. Patient requires multidisciplinary heart team evaluation for surgical vs. TAVR approach."
    ]
}

async def example_basic_usage():
    """Example of basic usage with different query complexities"""
    print("=== Structural Heart LLM System - Basic Usage Examples ===\n")
    
    # Simulate API calls (in real usage, you would use the FastAPI client)
    for complexity, queries in EXAMPLE_QUERIES.items():
        print(f"\n--- {complexity.upper()} QUERIES ---")
        
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            
            # Simulate response
            response = simulate_llm_response(query, complexity)
            print(f"Model Used: {response['model_used']}")
            print(f"Response: {response['response']}")
            print(f"Cost: ${response['cost']:.4f}")
            print(f"Processing Time: {response['processing_time']:.3f}s")
            print(f"Cache Hit: {response['cache_hit']}")
            print(f"Complexity Score: {response['complexity_score']}")

def simulate_llm_response(query: str, complexity: str) -> Dict[str, Any]:
    """Simulate LLM response for demonstration"""
    # Simulate different models based on complexity
    model_mapping = {
        "basic": "basic",
        "intermediate": "intermediate", 
        "advanced": "advanced"
    }
    
    # Simulate costs
    cost_mapping = {
        "basic": 0.0001,
        "intermediate": 0.0005,
        "advanced": 0.001
    }
    
    # Simulate responses based on query content
    if "aortic" in query.lower():
        response_text = "Aortic valve analysis indicates normal structure and function."
    elif "mitral" in query.lower():
        response_text = "Mitral valve assessment shows normal leaflet motion and coaptation."
    elif "ejection" in query.lower():
        response_text = "Ejection fraction analysis reveals normal cardiac function."
    elif "stenosis" in query.lower():
        response_text = "Valvular stenosis assessment requires detailed echocardiographic evaluation."
    else:
        response_text = "Structural heart analysis shows normal cardiac anatomy and function."
    
    return {
        "model_used": model_mapping[complexity],
        "response": response_text,
        "cost": cost_mapping[complexity],
        "processing_time": 0.5 if complexity == "basic" else (1.0 if complexity == "intermediate" else 2.0),
        "cache_hit": False,  # Simulate cache miss for first run
        "complexity_score": 30 if complexity == "basic" else (100 if complexity == "intermediate" else 200)
    }

def example_cost_optimization():
    """Example showing cost optimization strategies"""
    print("\n=== Cost Optimization Examples ===\n")
    
    # Example queries with cost analysis
    cost_examples = [
        "What is aortic valve stenosis?",
        "Patient with severe aortic stenosis measuring 0.8 cm² and ejection fraction 30%",
        "Complex multi-valvular disease requiring surgical intervention"
    ]
    
    for i, query in enumerate(cost_examples, 1):
        print(f"\nQuery {i}: {query}")
        
        # Simulate cost analysis for different models
        cost_analysis = simulate_cost_analysis(query)
        
        print("Cost Analysis:")
        for model, cost_info in cost_analysis["model_costs"].items():
            recommended = " (RECOMMENDED)" if cost_info["recommended"] else ""
            print(f"  {model}: ${cost_info['estimated_cost']:.4f}{recommended}")
        
        print(f"Recommended Model: {cost_analysis['recommended_model']}")

def simulate_cost_analysis(query: str) -> Dict[str, Any]:
    """Simulate cost analysis for different models"""
    # Simple cost estimation based on query length and complexity
    words = len(query.split())
    
    costs = {
        "basic": {"estimated_cost": words * 0.0001, "recommended": False},
        "intermediate": {"estimated_cost": words * 0.0005, "recommended": False},
        "advanced": {"estimated_cost": words * 0.001, "recommended": False}
    }
    
    # Determine recommended model based on query complexity
    if "complex" in query.lower() or "multi" in query.lower():
        recommended = "advanced"
    elif "severe" in query.lower() or "moderate" in query.lower():
        recommended = "intermediate"
    else:
        recommended = "basic"
    
    costs[recommended]["recommended"] = True
    
    return {
        "model_costs": costs,
        "recommended_model": recommended
    }

def example_caching_strategy():
    """Example showing caching benefits"""
    print("\n=== Caching Strategy Examples ===\n")
    
    # Simulate repeated queries
    repeated_queries = [
        "What is aortic valve stenosis?",
        "What is aortic valve stenosis?",  # Same query - should hit cache
        "Patient with aortic valve disease",
        "What is aortic valve stenosis?"   # Same query again
    ]
    
    for i, query in enumerate(repeated_queries, 1):
        print(f"\nQuery {i}: {query}")
        
        # Simulate cache behavior
        if i == 1 or i == 4:  # First and third occurrence
            cache_hit = False
            processing_time = 1.5
            cost = 0.0005
        else:  # Second occurrence (cache hit)
            cache_hit = True
            processing_time = 0.1
            cost = 0.0001  # Reduced cost for cache hit
        
        print(f"Cache Hit: {cache_hit}")
        print(f"Processing Time: {processing_time:.3f}s")
        print(f"Cost: ${cost:.4f}")
        
        if cache_hit:
            print("✓ Cached response - significant cost and time savings!")

def example_api_usage():
    """Example of API usage with FastAPI client"""
    print("\n=== API Usage Examples ===\n")
    
    # Example API requests (commented out as this is for demonstration)
    api_examples = [
        {
            "endpoint": "POST /query",
            "request": {
                "query": "What is aortic valve stenosis?",
                "include_analysis": True
            },
            "description": "Process a basic query with analysis"
        },
        {
            "endpoint": "GET /models/status",
            "request": {},
            "description": "Get status of all loaded models"
        },
        {
            "endpoint": "GET /cache/stats",
            "request": {},
            "description": "Get cache statistics"
        },
        {
            "endpoint": "GET /performance",
            "request": {},
            "description": "Get performance metrics"
        }
    ]
    
    for example in api_examples:
        print(f"Endpoint: {example['endpoint']}")
        print(f"Description: {example['description']}")
        if example['request']:
            print(f"Request: {json.dumps(example['request'], indent=2)}")
        print()

def example_security_and_monitoring():
    """Example of security and monitoring features"""
    print("\n=== Security and Monitoring Examples ===\n")
    
    security_features = [
        "API Key Authentication",
        "Rate Limiting (100 requests/minute)",
        "Request Validation",
        "Error Handling",
        "Structured Logging"
    ]
    
    monitoring_features = [
        "Prometheus Metrics",
        "Cache Hit/Miss Tracking",
        "Model Performance Monitoring",
        "Cost Tracking",
        "Health Checks"
    ]
    
    print("Security Features:")
    for feature in security_features:
        print(f"  ✓ {feature}")
    
    print("\nMonitoring Features:")
    for feature in monitoring_features:
        print(f"  ✓ {feature}")

def main():
    """Run all examples"""
    print("Structural Heart LLM System - Usage Examples")
    print("=" * 50)
    
    # Run examples
    asyncio.run(example_basic_usage())
    example_cost_optimization()
    example_caching_strategy()
    example_api_usage()
    example_security_and_monitoring()
    
    print("\n" + "=" * 50)
    print("Examples completed successfully!")
    print("\nTo run the actual system:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Start Redis server")
    print("3. Run: python main.py")
    print("4. Access API at: http://localhost:8000")

if __name__ == "__main__":
    main() 