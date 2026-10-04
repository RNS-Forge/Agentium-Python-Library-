"""Master Test Runner for Agentium v2.

Executes all unit and integration test suites covering Milestones 0 through 6:
- M0: Foundation & Core Runtime (10 suites)
- M1: Run Fingerprint & Drift CI Gate (2 suites)
- M2: Developer Experience & Health: init & doctor (1 suite)
- M3: Context Integrity: Pin Re-injection & Soak Test (2 suites)
- M4: Multi-Agent Trust: Claims, Lineage Graph, Handoff, Action Gate (4 suites)
- M5: Framework Adapters: LangGraph, CrewAI, OpenAI Agents (1 suite)
- M6: Experimental Acceleration: Speculative Read-Only Prefetch (1 suite)

Total: 21 comprehensive test suites.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_V2_DIR = PROJECT_ROOT / "test" / "v2"
SRC_DIR = PROJECT_ROOT / "src"

TEST_SUITES = [
    # M0: Foundation & Core Runtime
    ("M0: Events & JSONL Store", "test_events.py"),
    ("M0: Canonical JSON & Hashing", "test_canonical_hashing.py"),
    ("M0: Secret Redaction Engine", "test_redaction.py"),
    ("M0: Run Context & Scopes", "test_run_context.py"),
    ("M0: Tool Decorator & Registry", "test_tool_decorator.py"),
    ("M0: Config Loader & Env Overrides", "test_config.py"),
    ("M0: Zero Dependency Pledge", "test_zero_deps.py"),
    ("M0: OpenTelemetry Lazy Exporter", "test_otel.py"),
    ("M0: CLI Parser & Dispatch", "test_cli_basic.py"),
    ("M0: v1 Backward Compatibility", "test_v1_backward_compat.py"),
    # M1: Run Fingerprint & Drift CI Gate
    ("M1: Run Fingerprint & Hashing", "test_fingerprint.py"),
    ("M1: Drift CI Gate & Lock Diffs", "test_drift_gate.py"),
    # M2: Developer Experience & Health
    ("M2: Init & Doctor Health Checks", "test_init_doctor.py"),
    # M3: Context Integrity & Compaction
    ("M3: Pin Store & Compaction Guard", "test_pin_guard.py"),
    ("M3: Compaction Soak Test Harness", "test_soak.py"),
    # M4: Multi-Agent Trust & Lineage
    ("M4: Claims & Peer-Agreement Defense", "test_lineage_claims.py"),
    ("M4: Multi-Agent Lineage Graph", "test_lineage_graph.py"),
    ("M4: Handoff Contract & Linter", "test_handoff.py"),
    ("M4: Action Gate (Shadow & Enforce)", "test_action_gate.py"),
    # M5: Framework Adapters
    ("M5: Framework Adapters (Lazy)", "test_adapters.py"),
    # M5b: Hub Universal Wrapper, Facade, Plugins & Tier-1 Recipes
    ("M5b: Hub Universal Wrapper (wrap / wrap_async)", "test_hub_wrap.py"),
    ("M5b: Hub Facade & Plugins (use / discover)", "test_hub_facade_plugins.py"),
    ("M5b: Hub Recipes Batch 1 (R01, R03, R05, R06, R08)", "test_hub_recipes_batch1.py"),
    ("M5b: Hub Recipes Batch 2 (R10, R23, R15, R02, R25)", "test_hub_recipes_batch2.py"),
    ("M5b: Hub Recipes Batch 3 (R22, R27, R28, R39)", "test_hub_recipes_batch3.py"),
    ("M5b: Hub Recipes Batch 4 (R42, R43, R44, R45, R51, R58)", "test_hub_recipes_tier1_final.py"),
    # M6: Experimental Acceleration
    ("M6: Speculative Read-Only Prefetch", "test_prefetch.py"),
]


def main() -> int:
    print("=" * 70)
    print("RUNNING AGENTIUM V2 MASTER TEST SUITE (ALL 10 FEATURES)")
    print("=" * 70)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else "")

    results = []
    total_start = time.time()

    for description, script_name in TEST_SUITES:
        script_path = TEST_V2_DIR / script_name
        if not script_path.exists():
            print(f"[MISSING] {script_name}")
            results.append((description, script_name, "MISSING", 0.0, "File not found"))
            continue

        print(f"\n>> Executing {script_name} ({description})...")
        t0 = time.time()
        res = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        duration = time.time() - t0

        if res.returncode == 0:
            print(f"[PASS] {script_name} ({duration:.2f}s)")
            results.append((description, script_name, "PASS", duration, ""))
        else:
            print(f"[FAIL] {script_name} ({duration:.2f}s)")
            err_msg = res.stderr or res.stdout
            print(f"Error details:\n{err_msg}")
            results.append((description, script_name, "FAIL", duration, err_msg))

    total_duration = time.time() - total_start

    print("\n" + "=" * 70)
    print("AGENTIUM V2 MASTER TEST REPORT SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, _, status, _, _ in results if status == "PASS")
    total_count = len(results)

    for desc, script_name, status, duration, _ in results:
        badge = f"[{status}]"
        print(f"{badge:8} {script_name:28} : {desc:32} ({duration:.2f}s)")

    print("-" * 70)
    print(f"Total Suites : {total_count}")
    print(f"Passed       : {passed_count}")
    print(f"Failed       : {total_count - passed_count}")
    print(f"Duration     : {total_duration:.2f}s")
    print("=" * 70)

    if passed_count == total_count:
        print("ALL TESTS PASSED - AGENTIUM V2 FULLY VERIFIED [100% SUCCESS]")
        return 0
    else:
        print("SOME TESTS FAILED. Please review the details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
