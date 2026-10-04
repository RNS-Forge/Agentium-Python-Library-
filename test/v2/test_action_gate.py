"""Unit tests for F4: Action Gate (Shadow & Enforce Mode)."""
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
from agentium.lineage.claims import Claim
from agentium.lineage.gate import ActionBlockedError, ActionGate, guarded


class TestActionGate(unittest.TestCase):
    def test_read_and_write_permitted(self):
        gate = ActionGate(mode="enforce")
        ok_read, _ = gate.evaluate("read_file", effect="read")
        self.assertTrue(ok_read)

        ok_write, _ = gate.evaluate("write_file", effect="write")
        self.assertTrue(ok_write)

    def test_destructive_enforce_blocks_unauthorized(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = EventWriter(run_id="gate_test_1", events_dir=tmp_dir)
            gate = ActionGate(mode="enforce", event_writer=writer)

            def drop_table(tbl: str):
                return f"Dropped {tbl}"

            # Unauthorized call must raise ActionBlockedError
            with self.assertRaises(ActionBlockedError):
                gate.execute_guarded(drop_table, "destructive", "users")

            # Check that block event was recorded
            reader = EventReader(run_id="gate_test_1", events_dir=tmp_dir)
            events = reader.read_all()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].type, "action_gate_block")

    def test_destructive_authorized_by_human(self):
        gate = ActionGate(mode="enforce")
        def delete_all():
            return "deleted"

        res = gate.execute_guarded(delete_all, "destructive", human_confirmed=True)
        self.assertEqual(res, "deleted")

    def test_destructive_authorized_by_verified_claim(self):
        gate = ActionGate(mode="enforce")
        verified_claim = Claim(id="c_auth", statement="User requested database reset", status="verified", confidence=0.95)

        def reset_db():
            return "reset_ok"

        res = gate.execute_guarded(reset_db, "destructive", claims=[verified_claim])
        self.assertEqual(res, "reset_ok")

    def test_shadow_mode_logs_without_raising(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = EventWriter(run_id="shadow_test", events_dir=tmp_dir)
            gate = ActionGate(mode="shadow", event_writer=writer)

            def rm_rf():
                return "executed_in_shadow"

            # In shadow mode, does NOT raise
            result = gate.execute_guarded(rm_rf, "destructive")
            self.assertEqual(result, "executed_in_shadow")

            # But emits action_gate_shadow_block event
            reader = EventReader(run_id="shadow_test", events_dir=tmp_dir)
            events = reader.read_all()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].type, "action_gate_shadow_block")

    def test_guarded_decorator(self):
        gate = ActionGate(mode="enforce")

        @guarded(gate=gate, effect="destructive")
        def dangerous_action():
            return "success"

        with self.assertRaises(ActionBlockedError):
            dangerous_action()

        # Authorize with human confirmation
        ok_res = dangerous_action(__human_confirmed__=True)
        self.assertEqual(ok_res, "success")


if __name__ == "__main__":
    unittest.main()
