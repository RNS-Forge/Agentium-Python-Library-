import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.optimizer import Optimizer, OptimizationConfig, OptimizationType

def test_optimizer():
    print("=== Testing Optimizer ===")
    optimizer = Optimizer()
    
    # 1. Text Optimization
    sample_text = "In order to optimize this, we utilize a very large amount of really unnecessary redundant words in the text."
    opt_text_res = optimizer.optimize(sample_text, optimization_type=OptimizationType.TEXT)
    print("Optimized Text Result:", opt_text_res.get("text", opt_text_res))
    print("Improvements:", opt_text_res.get("improvements", []))
    assert opt_text_res is not None, "Text optimization failed"
    
    # 2. Code Optimization
    sample_code = """
def sample_func():
    a = [i for i in range(10)]
    return a
"""
    opt_code_res = optimizer.optimize(sample_code, optimization_type=OptimizationType.CODE)
    print("Optimized Code Result:", opt_code_res.get("code", opt_code_res))
    
    # 3. JSON Optimization
    sample_json = '{"name": "Agentium", "version": "1.1.0", "empty": null, "list": [1, 2]}'
    opt_json_res = optimizer.optimize(sample_json, optimization_type=OptimizationType.JSON)
    print("Optimized JSON Result:", opt_json_res.get("json", opt_json_res))
    
    print("Result: PASS\n")

if __name__ == "__main__":
    test_optimizer()
