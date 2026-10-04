"""Unit and integration tests for F6: Compaction Soak Test Harness."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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

from agentium.pin.soak import (
    LastNCompactor,
    StubSummarizer,
    TruncateCompactor,
    assert_pins_survive,
    soak,
)
from agentium.pin.store import PinStore


class TestSoakHarness(unittest.TestCase):
    def test_compactors_direct(self):
        msgs = [{"role": "user", "content": f"msg {i}"} for i in range(10)]

        # Truncate
        trunc = TruncateCompactor(drop_count=3)
        res_trunc = trunc(msgs)
        self.assertEqual(len(res_trunc), 7)
        self.assertEqual(res_trunc[0]["content"], "msg 3")

        # LastN
        last_n = LastNCompactor(keep_last=4)
        res_last = last_n(msgs)
        self.assertEqual(len(res_last), 4)
        self.assertEqual(res_last[0]["content"], "msg 6")

        # StubSummarizer
        summarizer = StubSummarizer(keep_recent=2)
        res_sum = summarizer(msgs)
        self.assertEqual(len(res_sum), 3)
        self.assertIn("CONVERSATION SUMMARY", res_sum[0]["content"])
        self.assertEqual(res_sum[-1]["content"], "msg 9")

    def test_soak_run_with_different_compactors(self):
        # Soak with LastNCompactor
        rep1 = soak(compactor=LastNCompactor(keep_last=4), num_turns=15, pin_interval=3)
        self.assertTrue(rep1.all_passed)
        self.assertGreater(rep1.compactions_triggered, 0)
        self.assertEqual(rep1.pins_survived, rep1.pins_injected)

        # Soak with TruncateCompactor
        rep2 = soak(compactor=TruncateCompactor(drop_count=4), num_turns=15, pin_interval=3)
        self.assertTrue(rep2.all_passed)
        self.assertEqual(rep2.pins_survived, rep2.pins_injected)

        # Soak with StubSummarizer
        rep3 = soak(compactor=StubSummarizer(keep_recent=3), num_turns=15, pin_interval=3)
        self.assertTrue(rep3.all_passed)
        self.assertEqual(rep3.pins_survived, rep3.pins_injected)

    def test_assert_pins_survive(self):
        store = PinStore()
        store.add("k1", "Must retain database URL")

        # Surviving messages
        good_messages = [{"role": "system", "content": "[ACTIVE CONTEXT PINS]\n- [k1]: Must retain database URL"}]
        assert_pins_survive(good_messages, store)  # Should not raise

        # Missing messages
        bad_messages = [{"role": "system", "content": "Just a general prompt"}]
        with self.assertRaises(AssertionError):
            assert_pins_survive(bad_messages, store)

    def test_cli_soak_and_pins(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(SRC_DIR) + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else "")

            # Run 'agentium soak --json'
            res_soak = subprocess.run(
                [sys.executable, "-m", "agentium.cli.main", "soak", "--json"],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_soak.returncode, 0)
            data = json.loads(res_soak.stdout)
            self.assertTrue(data["all_passed"])
            self.assertEqual(data["turns"], 20)

            # Run 'agentium pins render'
            res_pins = subprocess.run(
                [sys.executable, "-m", "agentium.cli.main", "pins", "render"],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_pins.returncode, 0)


if __name__ == "__main__":
    unittest.main()
