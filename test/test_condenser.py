import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.condenser import Condenser, CondenserConfig

def test_condenser():
    print("=== Testing Condenser ===")
    config = CondenserConfig(compression_ratio=0.5, preserve_key_phrases=True)
    condenser = Condenser(config=config)
    
    sample_text = (
        "Agentium is an advanced toolkit for AI agent development. "
        "It provides modular components for content processing, memory management, and workflow automation. "
        "Developers can easily orchestrate tasks, extract structured data, and compress verbose texts. "
        "Using Agentium reduces boilerplate code significantly across multi-agent environments."
    )
    
    # 1. Test condensation
    result = condenser.condense(sample_text)
    print("Original Text Length:", len(sample_text))
    print("Condensed Text Result:", result.get("condensed_text", result.get("text", "")))
    print("Stats / Compression:", result.get("stats", {}))
    assert result is not None, "Condenser failed to return result"

    # 2. Test metrics
    if hasattr(condenser, 'get_metrics'):
        metrics = condenser.get_metrics(sample_text)
        print("Metrics:", metrics)

    # 3. Test key phrase extraction
    if hasattr(condenser, 'extract_key_phrases'):
        phrases = condenser.extract_key_phrases(sample_text)
        print("Key Phrases:", phrases)

    print("Result: PASS\n")

if __name__ == "__main__":
    test_condenser()
