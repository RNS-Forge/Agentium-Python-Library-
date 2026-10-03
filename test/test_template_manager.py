import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.template_manager import TemplateManager, TemplateType

def test_template_manager():
    print("=== Testing TemplateManager ===")
    tm = TemplateManager()
    
    # 1. Text Template
    template_str = "Hello {{ user }}, welcome to {{ system }} v{{ version }}!"
    tid = tm.create_template("welcome_msg", template_str, template_type=TemplateType.TEXT)
    print("Created Template ID:", tid)
    
    rendered = tm.render(tid, {"user": "Alice", "system": "Agentium", "version": "1.1.0"})
    print("Rendered Text:", rendered)
    assert "Hello Alice, welcome to Agentium v1.1.0!" in rendered
    
    # 2. Markdown Report Template
    md_template = "# Report for {{ project }}\n\nStatus: **{{ status }}**\nScore: {{ score }}"
    tid_md = tm.create_template("md_report", md_template, template_type=TemplateType.MARKDOWN)
    rendered_md = tm.render(tid_md, {"project": "Agentium Testing", "status": "Passing", "score": 100})
    print("Rendered Markdown:\n", rendered_md)
    assert "**Passing**" in rendered_md

    print("Result: PASS\n")

if __name__ == "__main__":
    test_template_manager()
