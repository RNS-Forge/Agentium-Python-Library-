import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.summarize_custom import CustomSummarizer, SummaryType, SummaryLength

def test_summarizer():
    print("=== Testing CustomSummarizer ===")
    summarizer = CustomSummarizer()
    
    text = (
        "Artificial intelligence agents are evolving rapidly. "
        "Modern agents utilize large language models for reasoning and tool use. "
        "Workflow orchestration allows agents to break complex problems into sequential tasks. "
        "Stateful memory ensures context is preserved across multiple turns of user conversation. "
        "Evaluation and testing frameworks ensure that agents behave reliably in production."
    )
    
    # 1. Extractive Summary
    ext_res = summarizer.summarize(text, summary_type=SummaryType.EXTRACTIVE, length=SummaryLength.SHORT)
    print("Extractive Summary Result:\n", ext_res.get("summary"))
    assert "summary" in ext_res and len(ext_res["summary"]) > 0
    
    # 2. Bullet Points Summary
    bullet_res = summarizer.summarize(text, summary_type=SummaryType.BULLET_POINTS)
    print("Bullet Points Summary Result:\n", bullet_res.get("summary"))
    assert "summary" in bullet_res
    
    # 3. Keyword Summary
    kw_res = summarizer.summarize(text, summary_type=SummaryType.KEYWORD)
    print("Keyword Summary Result:\n", kw_res.get("summary"))

    print("Result: PASS\n")

if __name__ == "__main__":
    test_summarizer()
