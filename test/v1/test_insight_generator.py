import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.insight_generator import InsightGenerator, InsightConfig

def test_insight_generator():
    print("=== Testing InsightGenerator ===")
    config = InsightConfig(confidence_threshold=0.5, max_insights=10)
    generator = InsightGenerator(config=config)
    
    # 1. Numeric data series with an obvious upward trend and an anomaly
    numeric_data = [10, 12, 14, 15, 18, 22, 25, 99, 29, 32]
    insights = generator.generate_insights(numeric_data)
    print(f"Generated {len(insights)} numeric insights:")
    for ins in insights:
        print(f" - [{ins.get('type')}] {ins.get('title')}: {ins.get('description')} (confidence: {ins.get('confidence')})")
    
    assert len(insights) > 0, "Expected at least one insight from numeric series"
    
    # 2. Text data
    text_data = "Sales increased by 40% in Q3. Revenue hit records. Customer churn dropped to 2%."
    text_insights = generator.generate_insights(text_data)
    print(f"Generated {len(text_insights)} text insights:")
    for ins in text_insights:
        print(f" - [{ins.get('type')}] {ins.get('title')}: {ins.get('description')}")

    print("Result: PASS\n")

if __name__ == "__main__":
    test_insight_generator()
