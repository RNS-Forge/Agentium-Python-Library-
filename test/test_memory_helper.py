import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.memory_helper import MemoryHelper, ContextScope

def test_memory_helper():
    print("=== Testing MemoryHelper ===")
    mem = MemoryHelper()
    
    # 1. Direct Store and Retrieve
    mem.store("user_theme", "dark", scope=ContextScope.USER)
    retrieved_theme = mem.retrieve("user_theme")
    print("Retrieved User Theme:", retrieved_theme)
    assert retrieved_theme == "dark", "Theme retrieval failed"
    
    # 2. Context Object
    ctx = mem.create_context("session_42")
    ctx.store("auth_token", "xyz-12345")
    retrieved_token = ctx.get("auth_token")
    print("Context Retrieved Token:", retrieved_token)
    assert retrieved_token == "xyz-12345", "Context token retrieval failed"
    
    # 3. Memory Stats
    stats = mem.get_memory_stats()
    print("Memory Stats:", stats)
    assert stats.get("total_entries", 0) > 0, "Expected non-zero total entries"

    print("Result: PASS\n")

if __name__ == "__main__":
    test_memory_helper()
