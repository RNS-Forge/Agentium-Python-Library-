"""Unit tests for Framework Adapters (Milestone 5)."""
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

from agentium.adapters import CrewAIAdapter, LangGraphAdapter, OpenAIAgentsAdapter
from agentium.core.events import EventReader, EventWriter
from agentium.lineage.gate import ActionBlockedError, ActionGate
from agentium.pin.store import PinStore


class TestAdapters(unittest.TestCase):
    def test_lazy_loading(self):
        # Simply importing the adapter classes works without raising
        self.assertIsNotNone(LangGraphAdapter)
        self.assertIsNotNone(CrewAIAdapter)
        self.assertIsNotNone(OpenAIAgentsAdapter)

    def test_missing_extras_import_error_message(self):
        # If framework missing, check_installed raises with actionable message
        adapter = LangGraphAdapter()
        try:
            adapter.check_installed()
        except ImportError as e:
            self.assertIn("pip install 'agentium[langgraph]'", str(e))

    def test_langgraph_node_wrapping_and_pins(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = EventWriter(run_id="lg_test", events_dir=tmp_dir)
            pin_store = PinStore()
            pin_store.add("scope", "Read only data analysis")

            adapter = LangGraphAdapter(pin_store=pin_store, event_writer=writer, enforce_pins=True)

            def sample_node(state):
                return {"messages": state["messages"] + [{"role": "assistant", "content": "Processed"}]}

            wrapped = adapter.wrap_node("analyst_node", sample_node)

            initial_state = {
                "messages": [
                    {"role": "user", "content": "Analyze dataset"}
                ]
            }

            final_state = wrapped(initial_state)

            # Messages must contain injected pin block
            corpus = " ".join(m["content"] for m in final_state["messages"])
            self.assertIn("[ACTIVE CONTEXT PINS]", corpus)
            self.assertIn("Read only data analysis", corpus)

            # Events written
            reader = EventReader(run_id="lg_test", events_dir=tmp_dir)
            events = reader.read_all()
            types = [e.type for e in events]
            self.assertIn("tool_call", types)
            self.assertIn("tool_result", types)

    def test_crewai_handoff_recording(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = EventWriter(run_id="crew_test", events_dir=tmp_dir)
            adapter = CrewAIAdapter(event_writer=writer)

            pkt = adapter.record_handoff(
                from_agent="researcher",
                to_agent="writer",
                task="Draft executive summary",
                constraints=["Max 500 words", "Include revenue metrics"],
            )

            self.assertEqual(pkt.from_agent, "researcher")
            self.assertEqual(pkt.to_agent, "writer")
            self.assertEqual(len(pkt.constraints), 2)

            reader = EventReader(run_id="crew_test", events_dir=tmp_dir)
            events = reader.read_all()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].type, "handoff")
            self.assertEqual(events[0].payload["from_agent"], "researcher")

    def test_openai_agents_tool_guarding(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = EventWriter(run_id="openai_test", events_dir=tmp_dir)
            gate = ActionGate(mode="enforce", event_writer=writer)
            adapter = OpenAIAgentsAdapter(gate=gate, event_writer=writer)

            def drop_cache(cache_id: str):
                return f"Dropped {cache_id}"

            guarded_fn = adapter.guard_tool(drop_cache, effect="destructive")

            # Unauthorized: raises ActionBlockedError
            with self.assertRaises(ActionBlockedError):
                guarded_fn(cache_id="c_1")

            # Authorized with human confirmation
            res = guarded_fn(cache_id="c_1", __human_confirmed__=True)
            self.assertEqual(res, "Dropped c_1")


if __name__ == "__main__":
    unittest.main()
