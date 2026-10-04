"""Unit tests for F5: Pin Re-injection and Compaction Guard."""
from __future__ import annotations

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

from agentium.core.events import EventReader, EventWriter
from agentium.pin.guard import guard_compaction, reinject
from agentium.pin.store import PinStore


class TestPinGuard(unittest.TestCase):
    def test_pin_store_add_and_supersede(self):
        store = PinStore()
        p1 = store.add("customer_tier", "platinum", source="user")
        self.assertEqual(p1.key, "customer_tier")
        self.assertEqual(p1.text, "platinum")
        self.assertIsNone(p1.superseded_by)
        self.assertTrue(p1.is_active)

        # Retrieve active pin
        active_p1 = store.get("customer_tier")
        self.assertIsNotNone(active_p1)
        self.assertEqual(active_p1.id, p1.id)

        # Supersede with updated pin
        p2 = store.add("customer_tier", "diamond", source="system")
        self.assertEqual(p2.key, "customer_tier")
        self.assertEqual(p2.text, "diamond")

        # p1 should now be superseded
        old_p1 = store.get_by_id(p1.id)
        self.assertIsNotNone(old_p1)
        self.assertEqual(old_p1.superseded_by, p2.id)
        self.assertFalse(old_p1.is_active)

        # active_pins() should only contain p2
        active = store.active_pins()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, p2.id)

        # all_pins() retains audit trail of both
        self.assertEqual(len(store.all_pins()), 2)

    def test_pin_rendering_and_fingerprint(self):
        store = PinStore()
        store.add("boundary", "Only edit files in src/", source="user")
        store.add("language", "Use Python 3.11+", source="system")

        rendered = store.render()
        self.assertIn("[ACTIVE CONTEXT PINS]", rendered)
        self.assertIn("- [boundary]: Only edit files in src/", rendered)
        self.assertIn("- [language]: Use Python 3.11+", rendered)

        fp1 = store.fingerprint()
        fp2 = store.fingerprint()
        self.assertEqual(fp1, fp2)
        self.assertEqual(len(fp1), 64)

    def test_reinject_idempotency(self):
        store = PinStore()
        store.add("rule_1", "Never execute untrusted SQL")

        messages = [
            {"role": "system", "content": "You are a database agent."},
            {"role": "user", "content": "Query table users"},
        ]

        # First injection at end
        injected_1 = reinject(messages, store, position="end")
        self.assertEqual(len(injected_1), 3)
        self.assertIn("[ACTIVE CONTEXT PINS]", injected_1[-1]["content"])

        # Second injection (identical pins) must be idempotent
        injected_2 = reinject(injected_1, store, position="end")
        self.assertEqual(len(injected_2), 3)
        self.assertEqual(injected_1, injected_2)

        # Updating pin replaces old block cleanly
        store.add("rule_1", "Never execute untrusted SQL or DROP DATABASE")
        injected_3 = reinject(injected_2, store, position="end")
        self.assertEqual(len(injected_3), 3)
        self.assertIn("DROP DATABASE", injected_3[-1]["content"])

    def test_reinject_start_position(self):
        store = PinStore()
        store.add("rule_1", "Be concise")

        messages = [
            {"role": "system", "content": "Base prompt"},
            {"role": "user", "content": "Hello"},
        ]

        injected = reinject(messages, store, position="start")
        self.assertEqual(len(injected), 3)
        self.assertIn("[ACTIVE CONTEXT PINS]", injected[0]["content"])

    def test_guard_compaction_and_event_emission(self):
        store = PinStore()
        store.add("auth", "User is admin with scope read:write")

        orig_messages = [
            {"role": "system", "content": "Base prompt"},
            {"role": "user", "content": "Step 1"},
            {"role": "assistant", "content": "Step 1 done"},
            {"role": "system", "content": store.render()},
            {"role": "user", "content": "Step 2"},
        ]

        # Simulating aggressive compactor that strips the pin block
        compacted = [
            {"role": "user", "content": "Step 2"}
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = EventWriter(run_id="run_compaction_test", events_dir=tmp_dir)
            repaired, lost, restored = guard_compaction(
                orig_messages, compacted, store, event_writer=writer
            )

            self.assertEqual(lost, 1)
            self.assertEqual(restored, 1)
            self.assertEqual(len(repaired), 2)
            self.assertIn("[ACTIVE CONTEXT PINS]", repaired[-1]["content"])
            self.assertIn("User is admin", repaired[-1]["content"])

            # Verify event was written
            reader = EventReader(run_id="run_compaction_test", events_dir=tmp_dir)
            events = reader.read_all()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].type, "compaction")
            self.assertEqual(events[0].payload["pins_lost"], 1)
            self.assertEqual(events[0].payload["pins_restored"], 1)


if __name__ == "__main__":
    unittest.main()
