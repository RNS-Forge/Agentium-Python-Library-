"""Unit and integration tests for Milestone 2 (F9: agentium init and agentium doctor)."""
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

from agentium.cli.doctor_cmd import run_doctor
from agentium.cli.init_cmd import detect_frameworks, run_init


class TestInitDoctor(unittest.TestCase):
    def test_framework_detection_static_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            # Create a requirements.txt with langgraph
            (tmp / "requirements.txt").write_text("langgraph>=0.1.0\npydantic\n", encoding="utf-8")
            # Create a python file with crewai import
            (tmp / "agent.py").write_text("from crewai import Agent, Task\n", encoding="utf-8")

            detected = detect_frameworks(tmp)
            self.assertIn("langgraph", detected)
            self.assertIn("crewai", detected)

    def test_init_dry_run_and_execution(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)

            # Dry run: should not create file
            code, msg = run_init(tmp, dry_run=True)
            self.assertEqual(code, 0)
            self.assertFalse((tmp / "agentium.toml").exists())
            self.assertIn("Proposed agentium.toml diff", msg)

            # Execution: should create file and events dir
            code, msg = run_init(tmp, dry_run=False)
            self.assertEqual(code, 0)
            self.assertTrue((tmp / "agentium.toml").exists())
            self.assertTrue((tmp / ".agentium" / "events").exists())

            # Without --force, re-init must fail
            code_fail, msg_fail = run_init(tmp, dry_run=False, force=False)
            self.assertEqual(code_fail, 1)
            self.assertIn("already exists", msg_fail)

            # With --force, re-init succeeds
            code_force, _ = run_init(tmp, dry_run=False, force=True)
            self.assertEqual(code_force, 0)

    def test_doctor_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)

            # Fresh directory (no config, no lock) -> exit code 0 because warnings don't fail without --strict
            code, report = run_doctor(tmp, strict=False)
            self.assertEqual(code, 0)
            self.assertIn("Python Version", report)
            self.assertIn("Configuration File", report)
            self.assertIn("Baseline Lock File", report)

            # With --strict, missing lock / config triggers exit code 1
            code_strict, report_strict = run_doctor(tmp, strict=True)
            self.assertEqual(code_strict, 1)

            # Test JSON format
            code_json, report_json = run_doctor(tmp, as_json=True)
            data = json.loads(report_json)
            self.assertEqual(data["exit_code"], 0)
            self.assertEqual(len(data["checks"]), 9)

    def test_cli_subcommands(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            env = os.environ.copy()
            env["PYTHONPATH"] = str(SRC_DIR) + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else "")

            # Run 'agentium init --dry-run'
            res = subprocess.run(
                [sys.executable, "-m", "agentium.cli.main", "init", "--dry-run"],
                cwd=str(tmp),
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res.returncode, 0)

            # Run 'agentium init'
            res = subprocess.run(
                [sys.executable, "-m", "agentium.cli.main", "init"],
                cwd=str(tmp),
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res.returncode, 0)
            self.assertTrue((tmp / "agentium.toml").exists())

            # Run 'agentium doctor --json'
            res = subprocess.run(
                [sys.executable, "-m", "agentium.cli.main", "doctor", "--json"],
                cwd=str(tmp),
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res.returncode, 0)
            doc_data = json.loads(res.stdout)
            self.assertIn("checks", doc_data)


if __name__ == "__main__":
    unittest.main()
