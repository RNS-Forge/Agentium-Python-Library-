"""Implementation of 'agentium doctor' CLI command (F9).

Runs a 9-point environment, configuration, and lineage health check.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import find_config_file, load_config
from ..core.events import EventReader


@dataclass
class CheckResult:
    point: int
    name: str
    status: str  # "PASS", "WARN", "FAIL", "INFO"
    message: str
    details: Optional[Dict[str, Any]] = None


def check_python_version() -> CheckResult:
    major, minor = sys.version_info.major, sys.version_info.minor
    if (major, minor) >= (3, 11):
        return CheckResult(1, "Python Version", "PASS", f"Python {major}.{minor}.{sys.version_info.micro} (>= 3.11)")
    return CheckResult(1, "Python Version", "FAIL", f"Python {major}.{minor} is unsupported. Python >= 3.11 required.")


def check_config(project_root: Path) -> CheckResult:
    cfg_file = find_config_file(project_root)
    if cfg_file is None:
        return CheckResult(2, "Configuration File", "WARN", "No agentium.toml found. Default configuration will be used.")
    try:
        cfg = load_config(cfg_file)
        return CheckResult(2, "Configuration File", "PASS", f"agentium.toml found at {cfg_file} and valid.")
    except Exception as e:
        return CheckResult(2, "Configuration File", "FAIL", f"Error parsing {cfg_file}: {e}")


def check_events_dir(project_root: Path) -> CheckResult:
    cfg = load_config(project_root)
    ev_dir_path = Path(cfg.events.dir)
    if not ev_dir_path.is_absolute():
        ev_dir_path = project_root / ev_dir_path

    try:
        ev_dir_path.mkdir(parents=True, exist_ok=True)
        # Test writability with a temp file
        test_file = ev_dir_path / f".write_test_{os.getpid()}"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return CheckResult(3, "Event Directory", "PASS", f"Directory {ev_dir_path} exists and is writable.")
    except Exception as e:
        return CheckResult(3, "Event Directory", "FAIL", f"Event directory {ev_dir_path} is not writable: {e}")


def check_lock_file(project_root: Path, check_lock: bool, from_target: Optional[str]) -> CheckResult:
    lock_path = project_root / "agentium.lock"
    if not lock_path.is_file():
        return CheckResult(4, "Baseline Lock File", "WARN", "agentium.lock not found. Run 'agentium lock' to establish a baseline.")

    if not check_lock:
        return CheckResult(4, "Baseline Lock File", "PASS", f"Lock file found at {lock_path}.")

    # If --check-lock requested, run diff
    try:
        from ..fingerprint.diff import diff_fingerprints
        from ..fingerprint.fp import fingerprint
        from ..fingerprint.lock import read_lock_file

        lock = read_lock_file(lock_path)
        if not from_target and "source" in lock.metadata:
            from_target = lock.metadata["source"]

        if not from_target:
            return CheckResult(4, "Baseline Lock File", "WARN", "Lock file exists, but no target specified to check drift against.")

        from .main import _load_target_callable
        fn = _load_target_callable(from_target)
        cur_fp = fingerprint(**fn())
        report = diff_fingerprints(lock, cur_fp)
        if report.has_drift:
            return CheckResult(4, "Baseline Lock File", "FAIL", "Configuration drift detected against agentium.lock.")
        return CheckResult(4, "Baseline Lock File", "PASS", "Current agent components match agentium.lock baseline.")
    except Exception as e:
        return CheckResult(4, "Baseline Lock File", "FAIL", f"Error during lock check: {e}")


def check_pins_survival(project_root: Path) -> CheckResult:
    cfg = load_config(project_root)
    ev_dir_path = Path(cfg.events.dir)
    if not ev_dir_path.is_absolute():
        ev_dir_path = project_root / ev_dir_path

    if not ev_dir_path.exists():
        return CheckResult(5, "Pin Survival", "PASS", "No event logs present (fresh environment).")

    reader = EventReader(ev_dir_path)
    runs = reader.list_runs()
    recent_runs = runs[:5]

    lost_pins = False
    for run_id in recent_runs:
        events = reader.read_run(run_id)
        for ev in events:
            if ev.event_type == "compaction":
                data = ev.payload or {}
                if data.get("pins_lost", 0) > 0:
                    lost_pins = True
                    break

    if lost_pins:
        return CheckResult(5, "Pin Survival", "WARN", "Pin loss detected during compaction in recent runs.")
    return CheckResult(5, "Pin Survival", "PASS", f"No pin loss detected across recent runs ({len(recent_runs)} analyzed).")


def check_lineage_integrity(project_root: Path) -> CheckResult:
    cfg = load_config(project_root)
    ev_dir_path = Path(cfg.events.dir)
    if not ev_dir_path.is_absolute():
        ev_dir_path = project_root / ev_dir_path

    if not ev_dir_path.exists():
        return CheckResult(6, "Lineage Integrity", "PASS", "No event logs present (fresh environment).")

    reader = EventReader(ev_dir_path)
    runs = reader.list_runs()
    orphan_claims = False

    for run_id in runs[:5]:
        events = reader.read_run(run_id)
        claim_ids = set()
        dep_ids = set()
        for ev in events:
            if ev.event_type == "claim":
                cid = ev.payload.get("claim_id")
                if cid:
                    claim_ids.add(cid)
                for dep in ev.payload.get("dependencies", []):
                    dep_ids.add(dep)
        orphans = dep_ids - claim_ids
        if orphans:
            orphan_claims = True
            break

    if orphan_claims:
        return CheckResult(6, "Lineage Integrity", "WARN", "Orphan claim references found in recent run lineage.")
    return CheckResult(6, "Lineage Integrity", "PASS", "Lineage dependency integrity intact (no orphan claims).")


def check_action_gate(project_root: Path) -> CheckResult:
    cfg = load_config(project_root)
    mode = getattr(cfg.gate, "mode", "shadow")
    return CheckResult(7, "Action Gate Status", "INFO", f"Action gate configured in '{mode}' mode.")


def check_optional_extras() -> CheckResult:
    extras_status = []
    # Otel
    try:
        import opentelemetry  # type: ignore
        extras_status.append("otel: installed")
    except ImportError:
        extras_status.append("otel: not installed")

    # LangGraph
    try:
        import langgraph  # type: ignore
        extras_status.append("langgraph: installed")
    except ImportError:
        extras_status.append("langgraph: not installed")

    # CrewAI
    try:
        import crewai  # type: ignore
        extras_status.append("crewai: installed")
    except ImportError:
        extras_status.append("crewai: not installed")

    # OpenAI
    try:
        import openai  # type: ignore
        extras_status.append("openai: installed")
    except ImportError:
        extras_status.append("openai: not installed")

    return CheckResult(8, "Optional Extras", "INFO", f"Installed extras: {', '.join(extras_status)}")


def check_external_scanners() -> CheckResult:
    found_scanners = []
    for scanner in ["semgrep", "gitleaks", "snyk", "trufflehog"]:
        if shutil.which(scanner):
            found_scanners.append(scanner)

    if found_scanners:
        return CheckResult(
            9,
            "External Scanners",
            "INFO",
            f"Detected security scanner(s) in PATH: {', '.join(found_scanners)}. "
            f"Wire into CI to complement Agentium secret redaction.",
        )
    return CheckResult(
        9,
        "External Scanners",
        "INFO",
        "No external scanners found in PATH. Consider installing Gitleaks or Semgrep for static pre-commit secret scans.",
    )


def run_doctor(
    project_root: Path,
    strict: bool = False,
    check_lock: bool = False,
    from_target: Optional[str] = None,
    as_json: bool = False,
) -> Tuple[int, str]:
    """Run all 9 doctor checks and return (exit_code, output_text)."""
    checks = [
        check_python_version(),
        check_config(project_root),
        check_events_dir(project_root),
        check_lock_file(project_root, check_lock, from_target),
        check_pins_survival(project_root),
        check_lineage_integrity(project_root),
        check_action_gate(project_root),
        check_optional_extras(),
        check_external_scanners(),
    ]

    has_fail = any(c.status == "FAIL" for c in checks)
    has_warn = any(c.status == "WARN" for c in checks)

    if has_fail:
        exit_code = 1
    elif strict and has_warn:
        exit_code = 1
    else:
        exit_code = 0

    if as_json:
        payload = {
            "exit_code": exit_code,
            "strict": strict,
            "checks": [asdict(c) for c in checks],
        }
        return exit_code, json.dumps(payload, indent=2)

    lines = ["Agentium Doctor System Health Check", "=" * 45]
    for c in checks:
        badge = f"[{c.status:4}]"
        lines.append(f"{c.point}. {badge} {c.name}: {c.message}")

    lines.append("-" * 45)
    overall = "FAIL" if exit_code != 0 else "PASS"
    lines.append(f"Overall Result: {overall} (strict={strict})")
    return exit_code, "\n".join(lines) + "\n"
