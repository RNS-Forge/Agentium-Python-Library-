#!/usr/bin/env python3
"""
Agentium Library Test Script (Root verification runner).

Tests both v1 facade and core operations, plus runs the v2 and v1 test runners.
"""
from __future__ import annotations

import sys
import traceback
from typing import Dict, Any


def test_core_imports() -> bool:
    """Test that all core components can be imported."""
    print("[INFO] Testing core component imports...")
    try:
        from agentium import (
            Condenser, Optimizer, Rearranger, Extractor,
            Communicator, Translator, InsightGenerator,
            WorkflowHelper, TemplateManager, MemoryHelper,
            CustomSummarizer, LoggerUtils, Agentium
        )
        print("[PASS] All core components imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        traceback.print_exc()
        return False


def test_integration_availability() -> bool:
    """Test integration availability."""
    print("\n[INFO] Testing integration availability...")
    try:
        from agentium import (
            LANGCHAIN_INTEGRATION_AVAILABLE,
            LANGGRAPH_INTEGRATION_AVAILABLE,
            CREWAI_INTEGRATION_AVAILABLE
        )
        print(f"  LangChain Integration: {'[Available]' if LANGCHAIN_INTEGRATION_AVAILABLE else '[Not Available]'}")
        print(f"  LangGraph Integration: {'[Available]' if LANGGRAPH_INTEGRATION_AVAILABLE else '[Not Available]'}")
        print(f"  CrewAI Integration: {'[Available]' if CREWAI_INTEGRATION_AVAILABLE else '[Not Available]'}")
        return True
    except Exception as e:
        print(f"[FAIL] Integration check failed: {e}")
        return False


def test_core_functionality() -> bool:
    """Test basic functionality of core components."""
    print("\n[INFO] Testing core component functionality...")
    try:
        from agentium import Agentium

        agent = Agentium()
        print("[PASS] Agentium initialized successfully")

        test_content = (
            "This is a sample text for testing the Agentium library.\n"
            "It contains multiple sentences to demonstrate text processing capabilities.\n"
            "The library should be able to condense, optimize, and summarize this content effectively.\n"
            "We expect the workflow to process this text through multiple stages and produce meaningful results.\n"
        )

        print("  Testing basic workflow...")
        result = agent.process_content(test_content, workflow="basic")
        if result.get("success"):
            print("  [PASS] Basic workflow completed successfully")
            print(f"  Steps completed: {len(result.get('steps', []))}")
        else:
            print(f"  [FAIL] Basic workflow failed: {result.get('error', 'Unknown error')}")
            return False

        print("  Testing individual components...")
        condensed = agent.condenser.condense(test_content)
        print("  [PASS] Condenser completed")

        optimized = agent.optimizer.optimize(test_content)
        print("  [PASS] Optimizer completed")

        summarized = agent.summarizer.summarize(test_content)
        print("  [PASS] Summarizer completed")

        extracted = agent.extractor.extract(test_content)
        print("  [PASS] Extractor completed")

        context = agent.memory_helper.create_context("test_context")
        context.store("test_key", "test_value")
        retrieved = context.get("test_key")
        assert retrieved == "test_value"
        print("  [PASS] Memory storage & retrieval verified")
        return True
    except Exception as e:
        print(f"[FAIL] Functionality test failed: {e}")
        traceback.print_exc()
        return False


def test_logger_functionality() -> bool:
    """Test logging functionality."""
    print("\n[INFO] Testing logging functionality...")
    try:
        from agentium import LoggerUtils

        logger = LoggerUtils.get_logger("test_logger")
        logger.info("Test info message")
        logger.warning("Test warning message")
        print("[PASS] Logger functionality working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Logger test failed: {e}")
        return False


def run_all_tests() -> bool:
    """Run smoke tests and output summary."""
    print("=" * 60)
    print("STARTING AGENTIUM ROOT SMOKE TESTS")
    print("=" * 60)

    tests = [
        ("Core Imports", test_core_imports),
        ("Integration Availability", test_integration_availability),
        ("Core Functionality", test_core_functionality),
        ("Logger Functionality", test_logger_functionality),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"[FAIL] {test_name} crashed: {e}")

    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed}/{total} tests passed")
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)