"""Unit tests for F10: Speculative Read-Only Tool Prefetch (Experimental)."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentium.speed.prefetch import PrefetchManager, ToolPredictor


class TestPrefetch(unittest.TestCase):
    def test_disabled_by_default(self):
        manager = PrefetchManager(enabled=None)
        # Should be False unless AGENTIUM_EXPERIMENTAL_PREFETCH=1
        self.assertFalse(manager.is_active())

    def test_readonly_invariant_enforcement(self):
        """CRITICAL: NEVER prefetch write or destructive tools."""
        manager = PrefetchManager(enabled=True)

        call_count = 0
        def dangerous_tool(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Destructive tool
        ok_dest = manager.maybe_prefetch("dangerous_tool", dangerous_tool, effect="destructive", kwargs={"x": 5})
        self.assertFalse(ok_dest)
        self.assertEqual(call_count, 0)

        # Write tool
        ok_write = manager.maybe_prefetch("dangerous_tool", dangerous_tool, effect="write", kwargs={"x": 5})
        self.assertFalse(ok_write)
        self.assertEqual(call_count, 0)

        # Read tool: permitted
        ok_read = manager.maybe_prefetch("dangerous_tool", dangerous_tool, effect="read", kwargs={"x": 5})
        self.assertTrue(ok_read)
        self.assertEqual(call_count, 1)

    def test_prefetch_hit_and_consumption(self):
        manager = PrefetchManager(enabled=True)

        executions = 0
        def fetch_doc(doc_id):
            nonlocal executions
            executions += 1
            return f"Doc content for {doc_id}"

        # 1. Speculatively prefetch
        prefetched = manager.maybe_prefetch("fetch_doc", fetch_doc, effect="read", kwargs={"doc_id": "101"})
        self.assertTrue(prefetched)
        self.assertEqual(executions, 1)

        # 2. Actual invocation consumes cache without re-executing
        is_hit, result = manager.get_or_record_usage("fetch_doc", kwargs={"doc_id": "101"})
        self.assertTrue(is_hit)
        self.assertEqual(result, "Doc content for 101")
        self.assertEqual(executions, 1)  # Still 1!

        # 3. Next invocation must miss because entry was consumed
        is_hit2, _ = manager.get_or_record_usage("fetch_doc", kwargs={"doc_id": "101"})
        self.assertFalse(is_hit2)

    def test_ttl_expiration(self):
        # Manager with very short TTL
        manager = PrefetchManager(enabled=True, ttl_seconds=0.05)

        def get_time():
            return "time_data"

        manager.maybe_prefetch("get_time", get_time, effect="read", kwargs={})
        time.sleep(0.1)  # Allow TTL to elapse

        is_hit, _ = manager.get_or_record_usage("get_time", kwargs={})
        self.assertFalse(is_hit, "Expired entry must not be returned as hit")

    def test_circuit_breaker_auto_disable(self):
        manager = PrefetchManager(
            enabled=True,
            ttl_seconds=0.01,
            max_wasted_per_run=3,
        )

        def dummy_read(k):
            return f"v_{k}"

        # Cause 3 entries to expire and be wasted
        for i in range(3):
            manager.maybe_prefetch("dummy_read", dummy_read, effect="read", kwargs={"k": i})
        time.sleep(0.03)

        manager.reap_wasted()
        self.assertTrue(manager.circuit_broken)
        self.assertFalse(manager.is_active())

    def test_tool_predictor_markov(self):
        predictor = ToolPredictor()

        # Train transitions: search -> read_page (8 times), search -> calc (2 times)
        for _ in range(8):
            predictor.record_transition("search")
            predictor.record_transition("read_page")

        for _ in range(2):
            predictor.record_transition("search")
            predictor.record_transition("calc")

        # Given 'search', best prediction should be 'read_page' with 80% confidence
        prediction = predictor.predict_next("search", min_confidence=0.5)
        self.assertEqual(prediction, "read_page")


if __name__ == "__main__":
    unittest.main()
