#!/usr/bin/env python3
"""
Simplified Agentium Library Test Script.

Tests basic core functionality without external optional dependencies.
"""
from __future__ import annotations

import sys
import asyncio
import traceback


def test_minimal_imports() -> bool:
    """Test that basic components can be imported."""
    print("[INFO] Testing minimal imports...")
    try:
        from agentium.utils.logger_utils import LoggerUtils
        print("[PASS] LoggerUtils imported successfully")

        from agentium.core.memory_helper import MemoryHelper
        print("[PASS] MemoryHelper imported successfully")

        from agentium.core.template_manager import TemplateManager  
        print("[PASS] TemplateManager imported successfully")

        from agentium.core.workflow_helper import WorkflowHelper
        print("[PASS] WorkflowHelper imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Minimal import failed: {e}")
        traceback.print_exc()
        return False


def test_memory_functionality() -> bool:
    """Test memory functionality."""
    print("\n[INFO] Testing memory functionality...")
    try:
        from agentium.core.memory_helper import MemoryHelper, ContextScope

        mem = MemoryHelper()
        mem.store("user_theme", "dark", scope=ContextScope.USER)
        retrieved_theme = mem.retrieve("user_theme")
        assert retrieved_theme == "dark"

        ctx = mem.create_context("session_42")
        ctx.store("auth_token", "xyz-12345")
        retrieved_token = ctx.get("auth_token")
        assert retrieved_token == "xyz-12345"

        print("[PASS] Memory store/retrieve working")
        return True
    except Exception as e:
        print(f"[FAIL] Memory test failed: {e}")
        return False


def test_template_functionality() -> bool:
    """Test template functionality."""
    print("\n[INFO] Testing template functionality...")
    try:
        from agentium.core.template_manager import TemplateManager, TemplateType

        tm = TemplateManager()
        template_str = "Hello {{ user }}, welcome to {{ system }}!"
        tid = tm.create_template("welcome_msg", template_str, template_type=TemplateType.TEXT)
        rendered = tm.render(tid, {"user": "Alice", "system": "Agentium"})
        assert "Hello Alice, welcome to Agentium!" in rendered

        print("[PASS] Template rendering working")
        return True
    except Exception as e:
        print(f"[FAIL] Template test failed: {e}")
        return False


def test_workflow_functionality() -> bool:
    """Test workflow functionality."""
    print("\n[INFO] Testing workflow functionality...")
    try:
        from agentium.core.workflow_helper import WorkflowHelper, Task

        helper = WorkflowHelper()
        t1 = Task(id="task_1", name="Step1", function=lambda **kwargs: "step1 done")
        t2 = Task(id="task_2", name="Step2", function=lambda **kwargs: "step2 done", dependencies=["task_1"])

        workflow_id = helper.create_workflow("Mini Workflow", [t1, t2])
        res = asyncio.run(helper.execute_workflow(workflow_id))
        assert res.get("status") == "completed"

        print("[PASS] Workflow execution working")
        return True
    except Exception as e:
        print(f"[FAIL] Workflow test failed: {e}")
        return False


def test_logger_functionality() -> bool:
    """Test logger functionality."""
    print("\n[INFO] Testing logger functionality...")
    try:
        from agentium.utils.logger_utils import LoggerUtils

        logger = LoggerUtils.get_logger("test")
        logger.info("Test log message")
        print("[PASS] Logger working")
        return True
    except Exception as e:
        print(f"[FAIL] Logger test failed: {e}")
        return False


def run_minimal_tests() -> bool:
    """Run minimal test suite."""
    print("=" * 60)
    print("STARTING MINIMAL AGENTIUM TESTS")
    print("=" * 60)

    tests = [
        ("Minimal Imports", test_minimal_imports),
        ("Memory Functionality", test_memory_functionality),
        ("Template Functionality", test_template_functionality),
        ("Workflow Functionality", test_workflow_functionality),
        ("Logger Functionality", test_logger_functionality),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"[FAIL] {test_name} test crashed: {e}")

    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed}/{total} tests passed")
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    success = run_minimal_tests()
    sys.exit(0 if success else 1)