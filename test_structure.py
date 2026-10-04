#!/usr/bin/env python3
"""
Agentium Structure & Direct Module Verification.

Verifies repository layout, source distribution files, and direct module accessibility.
"""
from __future__ import annotations

import os
import sys
import traceback


def test_library_structure() -> bool:
    """Test that essential library files and directories exist."""
    print("[INFO] Testing library structure...")

    required_paths = [
        "pyproject.toml",
        "README.md",
        "requirements.txt",
        "agentium.toml",
        "src/agentium/__init__.py",
        "src/agentium/core/__init__.py",
        "src/agentium/core/events.py",
        "src/agentium/pin/store.py",
        "src/agentium/lineage/claims.py",
        "src/agentium/cli/main.py",
        "src/agentium/hub/__init__.py",
        "src/agentium/recipes/__init__.py",
        "src/agentium/_v1/__init__.py",
    ]

    missing = [path for path in required_paths if not os.path.exists(path)]
    if missing:
        print(f"[FAIL] Missing paths: {missing}")
        return False

    print(f"[PASS] All {len(required_paths)} required structural paths present")
    return True


def test_direct_imports() -> bool:
    """Test direct module imports via top-level agentium."""
    print("\n[INFO] Testing direct module imports...")
    try:
        from agentium.utils.logger_utils import LoggerUtils
        print("[PASS] LoggerUtils imported")

        from agentium.core.memory_helper import MemoryHelper
        print("[PASS] MemoryHelper imported")

        from agentium.core.events import EventWriter
        print("[PASS] EventWriter imported")

        from agentium.pin.store import PinStore
        print("[PASS] PinStore imported")

        return True
    except Exception as e:
        print(f"[FAIL] Direct import failed: {e}")
        traceback.print_exc()
        return False


def test_logger_direct() -> bool:
    """Test logger directly."""
    print("\n[INFO] Testing logger directly...")
    try:
        from agentium.utils.logger_utils import LoggerUtils

        logger = LoggerUtils.get_logger("test")
        logger.info("Direct test message")
        print("[PASS] Logger working directly")
        return True
    except Exception as e:
        print(f"[FAIL] Logger direct test failed: {e}")
        return False


def test_memory_direct() -> bool:
    """Test memory directly."""
    print("\n[INFO] Testing memory directly...")
    try:
        from agentium.core.memory_helper import MemoryHelper

        memory = MemoryHelper()
        context = memory.create_context("test")
        context.store("test_key", "test_value")
        retrieved = context.get("test_key")

        if retrieved == "test_value":
            print("[PASS] Memory store/retrieve working")
            return True
        else:
            print("[FAIL] Memory store/retrieve failed")
            return False
    except Exception as e:
        print(f"[FAIL] Memory direct test failed: {e}")
        return False


def run_direct_tests() -> bool:
    """Run direct tests."""
    print("=" * 60)
    print("STARTING DIRECT MODULE AND STRUCTURE TESTS")
    print("=" * 60)

    tests = [
        ("Library Structure", test_library_structure),
        ("Direct Imports", test_direct_imports),
        ("Logger Direct", test_logger_direct),
        ("Memory Direct", test_memory_direct),
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
    success = run_direct_tests()
    sys.exit(0 if success else 1)