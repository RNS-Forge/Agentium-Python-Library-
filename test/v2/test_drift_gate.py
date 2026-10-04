"""Unit tests for F8: Drift CI Gate (agentium.fingerprint lock & diff, and CLI)."""
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

from agentium.fingerprint.diff import diff_fingerprints
from agentium.fingerprint.fp import fingerprint
from agentium.fingerprint.lock import LockFile, read_lock_file, write_lock_file


class TestDriftGate(unittest.TestCase):
    def test_lock_file_read_write(self):
        fp = fingerprint(
            model="gpt-4o-mini",
            params={"temperature": 0.5},
            system_prompt="Test agent",
            tools=[{"name": "tool_a", "description": "desc a"}],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            lock_path = Path(tmp_dir) / "agentium.lock"
            write_lock_file(lock_path, fp, metadata={"author": "ci", "env": "prod"})
            self.assertTrue(lock_path.exists())

            read_lock = read_lock_file(lock_path)
            self.assertEqual(read_lock.version, 1)
            self.assertEqual(read_lock.combined, fp.combined)
            self.assertEqual(read_lock.components["model"], fp.model)
            self.assertEqual(read_lock.metadata["author"], "ci")

    def test_diff_no_drift(self):
        fp = fingerprint(
            model="claude-3-5-haiku",
            params={"temperature": 0.0},
            tools=[{"name": "lookup", "description": "Lookup table"}],
        )
        lock = LockFile(
            schema_version=1,
            combined_fingerprint=fp.combined,
            components=fp.components,
            tools=fp.tool_names,
        )
        report = diff_fingerprints(lock, fp)
        self.assertFalse(report.has_drift)
        self.assertFalse(report.tools_added)
        self.assertFalse(report.tools_removed)
        self.assertIn("NO DRIFT", report.to_text())
        self.assertIn("No Drift Detected", report.to_markdown())
        self.assertIn("<!-- agentium-drift -->", report.to_markdown())

    def test_diff_model_and_tool_drift(self):
        fp_baseline = fingerprint(
            model="gpt-4o",
            system_prompt="Helpful",
            tools=[
                {"name": "search", "description": "Search web", "parameters": {"type": "object"}},
                {"name": "calculator", "description": "Math", "parameters": {"type": "object"}},
            ],
        )
        lock = LockFile(
            schema_version=1,
            combined_fingerprint=fp_baseline.combined,
            components=fp_baseline.components,
            tools=fp_baseline.tool_names,
        )

        # In current: model changed, search description changed (non-structural), calculator removed, browse added
        fp_current = fingerprint(
            model="gpt-4o-2024-08-06",
            system_prompt="Helpful",
            tools=[
                {
                    "name": "search",
                    "description": "Search web updated",
                    "parameters": {"type": "object"},
                },
                {"name": "browse", "description": "Browse url", "parameters": {"type": "object"}},
            ],
        )

        report = diff_fingerprints(lock, fp_current)
        self.assertTrue(report.has_drift)

        self.assertIn("browse", report.tools_added)
        self.assertIn("calculator", report.tools_removed)
        self.assertFalse(report.component_diffs["model"].matches)
        self.assertTrue(report.tool_structural_changes)

        # Markdown format check
        md = report.to_markdown()
        self.assertIn("<!-- agentium-drift -->", md)
        self.assertIn("Drift Detected", md)
        self.assertIn("browse", md)
        self.assertIn("calculator", md)

        # JSON format check
        js = json.loads(report.to_json())
        self.assertTrue(js["has_drift"])
        self.assertIn("browse", js["tools_added"])
        self.assertIn("calculator", js["tools_removed"])

    def test_diff_description_only(self):
        fp1 = fingerprint(
            model="gpt-4o",
            tools=[{"name": "t1", "description": "Original description", "parameters": {"type": "object"}}],
        )
        lock = LockFile(
            schema_version=1,
            combined_fingerprint=fp1.combined,
            components=fp1.components,
            tools=fp1.tool_names,
        )
        fp2 = fingerprint(
            model="gpt-4o",
            tools=[{"name": "t1", "description": "New description", "parameters": {"type": "object"}}],
        )
        report = diff_fingerprints(lock, fp2)
        self.assertTrue(report.has_drift)
        self.assertTrue(report.tool_description_only_changes)
        self.assertFalse(report.tool_structural_changes)

    def test_cli_lock_and_check(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a dummy target module in tmp_path
            target_py = tmp_path / "dummy_agent.py"
            target_py.write_text(
                """
def get_target():
    return {
        "model": "test-model-v1",
        "system_prompt": "You are a test agent",
        "tools": [{"name": "echo", "description": "Echo input"}]
    }
""",
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["PYTHONPATH"] = str(SRC_DIR) + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else "")

            # Run 'agentium lock'
            res_lock = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agentium.cli.main",
                    "lock",
                    "--from",
                    "dummy_agent:get_target",
                ],
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_lock.returncode, 0, f"lock failed: {res_lock.stderr}")
            self.assertTrue((tmp_path / "agentium.lock").exists())

            # Run 'agentium check' -> should return 0 (no drift)
            res_check = subprocess.run(
                [sys.executable, "-m", "agentium.cli.main", "check"],
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_check.returncode, 0, f"check failed: {res_check.stderr}")
            self.assertIn("NO DRIFT", res_check.stdout)

            # Now modify target to cause drift
            target_py.write_text(
                """
def get_target():
    return {
        "model": "test-model-v2-drifted",
        "system_prompt": "You are a test agent",
        "tools": [{"name": "echo", "description": "Echo input"}]
    }
""",
                encoding="utf-8",
            )

            # Run 'agentium check --format json' -> should return 1 (drift detected)
            res_drift = subprocess.run(
                [sys.executable, "-m", "agentium.cli.main", "check", "--format", "json"],
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_drift.returncode, 1)
            parsed_drift = json.loads(res_drift.stdout)
            self.assertTrue(parsed_drift["has_drift"])


if __name__ == "__main__":
    unittest.main()
