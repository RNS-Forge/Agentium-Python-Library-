"""Unit tests for F2: Multi-Agent Lineage Graph."""
from __future__ import annotations

import sys
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

from agentium.core.events import Event
from agentium.lineage.graph import LineageGraph, diff_lineage


class TestLineageGraph(unittest.TestCase):
    def test_graph_construction_and_cycle_detection(self):
        graph = LineageGraph(run_id="run_1")
        graph.add_node("agent_a", "agent", "Planner")
        graph.add_node("agent_b", "agent", "Coder")
        graph.add_node("claim_1", "claim", "Architecture Approved")

        graph.add_edge("agent_a", "claim_1", "produces")
        graph.add_edge("claim_1", "agent_b", "depends_on")

        self.assertFalse(graph.has_cycle())

        # Introduce a cycle
        graph.add_edge("agent_b", "agent_a", "hands_off_to")
        self.assertTrue(graph.has_cycle())

    def test_blame_root_cause(self):
        graph = LineageGraph(run_id="run_1")
        graph.add_node("agent_alpha", "agent", "Alpha")
        graph.add_node("db_tool", "tool_call", "sql_query")
        graph.add_node("claim_user_exists", "claim", "User exists in DB", metadata={"statement": "User exists", "source_agent": "agent_alpha"})

        graph.add_edge("agent_alpha", "db_tool", "invokes")
        graph.add_edge("db_tool", "claim_user_exists", "verifies")

        blame = graph.blame("claim_user_exists")
        self.assertEqual(blame.claim_id, "claim_user_exists")
        self.assertEqual(blame.origin_agent, "agent_alpha")
        self.assertIn("db_tool", blame.root_tool_calls)
        self.assertTrue(blame.is_grounded)
        self.assertIn("db_tool", blame.to_text())

    def test_mermaid_and_markdown_rendering(self):
        graph = LineageGraph(run_id="run_1")
        graph.add_node("agent_1", "agent", "Search Agent")
        graph.add_node("claim_1", "claim", "Fact checked")
        graph.add_edge("agent_1", "claim_1", "produces")

        mermaid = graph.to_mermaid()
        self.assertIn("flowchart TD", mermaid)
        self.assertIn("Search Agent", mermaid)

        md = graph.to_markdown()
        self.assertIn("Multi-Agent Lineage Graph", md)
        self.assertIn("```mermaid", md)

    def test_graph_from_events(self):
        events = [
            Event(event_id=1, run_id="r1", type="claim", agent_id="agent_1", payload={"claim": {"id": "c1", "statement": "All clear", "source_agent": "agent_1"}}),
            Event(event_id=2, run_id="r1", type="tool_call", agent_id="agent_1", payload={"tool_name": "check_env"}),
            Event(event_id=3, run_id="r1", type="handoff", agent_id="agent_1", payload={"from_agent": "agent_1", "to_agent": "agent_2"}),
        ]

        graph = LineageGraph.from_events(events, run_id="r1")
        self.assertIn("c1", graph.nodes)
        self.assertIn("agent_1", graph.nodes)
        self.assertIn("agent_2", graph.nodes)

    def test_lineage_diff(self):
        g1 = LineageGraph(run_id="run_1")
        g1.add_node("c1", "claim", "claim 1", metadata={"status": "unverified"})
        g1.add_node("a1", "agent", "agent 1")
        g1.add_node("a2", "agent", "agent 2")
        g1.add_edge("a1", "a2", "hands_off_to")

        g2 = LineageGraph(run_id="run_2")
        g2.add_node("c1", "claim", "claim 1", metadata={"status": "verified"})  # status changed
        g2.add_node("c2", "claim", "claim 2", metadata={"status": "unverified"})  # added
        g2.add_node("a1", "agent", "agent 1")
        g2.add_node("a3", "agent", "agent 3")
        g2.add_edge("a1", "a3", "hands_off_to")  # handoff changed

        diff = diff_lineage(g1, g2)
        self.assertIn("c2", diff.claims_added)
        self.assertEqual(len(diff.claims_status_changed), 1)
        self.assertEqual(diff.claims_status_changed[0]["claim_id"], "c1")
        self.assertIn(("a1", "a3"), diff.handoffs_added)
        self.assertIn(("a1", "a2"), diff.handoffs_removed)


if __name__ == "__main__":
    unittest.main()
