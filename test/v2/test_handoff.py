"""Unit tests for F3: Handoff Contract and Packet Linter."""
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

from agentium.lineage.claims import Claim
from agentium.lineage.handoff import (
    HandoffOverflowError,
    HandoffPacket,
    enforce_handoff_size,
    lint_handoff,
)


class TestHandoff(unittest.TestCase):
    def test_handoff_creation_and_serialization(self):
        pkt = HandoffPacket(
            from_agent="planner",
            to_agent="coder",
            task="Implement feature A",
            constraints=["Must use Python 3.11", "No 3rd party deps"],
            claims=[Claim(id="c1", statement="Spec validated", status="verified")],
        )
        self.assertEqual(pkt.from_agent, "planner")
        d = pkt.to_dict()
        self.assertEqual(d["task"], "Implement feature A")
        rebuilt = HandoffPacket.from_dict(d)
        self.assertEqual(rebuilt.from_agent, "planner")
        self.assertEqual(len(rebuilt.claims), 1)

    def test_constraints_never_dropped_policy(self):
        """CRITICAL: Constraints must NEVER be dropped under any truncation policy."""
        huge_constraints = ["Constraint " + ("X" * 200) for _ in range(20)]
        pkt = HandoffPacket(
            from_agent="a",
            to_agent="b",
            task="Do work",
            constraints=huge_constraints,
            max_tokens=100,  # Far smaller than constraints alone
        )

        # Truncate unverified policy MUST NOT drop constraints
        with self.assertRaises(HandoffOverflowError):
            enforce_handoff_size(pkt, on_overflow="truncate_unverified")

        # Truncate oldest policy MUST NOT drop constraints
        with self.assertRaises(HandoffOverflowError):
            enforce_handoff_size(pkt, on_overflow="truncate_oldest")

    def test_truncate_unverified_claims(self):
        c_verified = Claim(id="v1", statement="Verified claim", status="verified")
        c_unverified = Claim(id="u1", statement="Unverified claim " * 50, status="unverified")

        pkt = HandoffPacket(
            from_agent="a",
            to_agent="b",
            task="Task",
            constraints=["Safe mode"],
            claims=[c_verified, c_unverified],
            max_tokens=200,
        )

        # Enforce truncation
        repaired = enforce_handoff_size(pkt, on_overflow="truncate_unverified")
        self.assertEqual(len(repaired.claims), 1)
        self.assertEqual(repaired.claims[0].id, "v1")
        self.assertEqual(repaired.constraints, ["Safe mode"])

    def test_lint_handoff_catches_issues(self):
        # 1. Circular handoff & missing constraints
        bad_pkt = HandoffPacket(
            from_agent="agent_1",
            to_agent="agent_1",  # self-handoff
            task="Some task",
            constraints=[],  # empty
            claims=[Claim(id="c1", statement="Dubious", status="unverified", confidence=0.95)],  # ungrounded high confidence
        )

        issues = lint_handoff(bad_pkt)
        codes = [i.code for i in issues]
        self.assertIn("CIRCULAR_HANDOFF", codes)
        self.assertIn("NO_CONSTRAINTS", codes)
        self.assertIn("UNGROUNDED_HIGH_CONFIDENCE_CLAIM", codes)


    def test_cli_handoff_lint(self):
        import json
        import os
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            pkt_file = Path(tmp_dir) / "packet.json"
            pkt = HandoffPacket(
                from_agent="a1",
                to_agent="a2",
                task="Safe task",
                constraints=["Constraint 1"],
            )
            pkt_file.write_text(pkt.to_json(), encoding="utf-8")

            env = os.environ.copy()
            env["PYTHONPATH"] = str(SRC_DIR) + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else "")

            res = subprocess.run(
                [sys.executable, "-m", "agentium.cli.main", "handoff", "lint", str(pkt_file)],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("No issues found", res.stdout)


if __name__ == "__main__":
    unittest.main()
