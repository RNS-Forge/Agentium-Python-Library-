from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..fingerprint.diff import diff_fingerprints
from ..fingerprint.fp import Fingerprint, fingerprint
from ..fingerprint.lock import LockFile, read_lock_file, write_lock_file


def _load_target_callable(target_str: str) -> Callable[[], Dict[str, Any]]:
    """Dynamically import module:callable target.
    SECURITY NOTICE: This executes user-specified Python code.
    """
    if ":" not in target_str:
        raise ValueError(
            f"Invalid target format '{target_str}'. Expected 'module:callable' (e.g. 'my_agent:get_fingerprint_target')."
        )
    mod_name, func_name = target_str.split(":", 1)
    # Ensure current working directory is on sys.path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    module = importlib.import_module(mod_name)
    target_fn = getattr(module, func_name, None)
    if target_fn is None or not callable(target_fn):
        raise AttributeError(f"Module '{mod_name}' has no callable attribute '{func_name}'.")
    return target_fn


def handle_lock(args: argparse.Namespace) -> int:
    if not args.from_target:
        sys.stderr.write("Error: --from <module:callable> is required for 'agentium lock'.\n")
        return 2

    try:
        fn = _load_target_callable(args.from_target)
        fp_kwargs = fn()
        if not isinstance(fp_kwargs, dict):
            sys.stderr.write(
                f"Error: Target callable '{args.from_target}' must return a dict of fingerprint kwargs, got {type(fp_kwargs)}.\n"
            )
            return 2

        fp = fingerprint(**fp_kwargs)
        lock_path = Path("agentium.lock")
        write_lock_file(lock_path, fp, metadata={"source": args.from_target})

        if getattr(args, "json", False):
            print(json.dumps({"status": "ok", "lock_file": str(lock_path), "combined": fp.combined}))
        else:
            print(f"Recorded baseline fingerprint to {lock_path} (combined: {fp.combined[:16]}...)")
        return 0
    except Exception as e:
        sys.stderr.write(f"Error creating lock file: {e}\n")
        return 2


def handle_check(args: argparse.Namespace) -> int:
    lock_path = Path("agentium.lock")
    if not lock_path.is_file():
        sys.stderr.write(f"Error: Baseline lock file not found at '{lock_path}'. Run 'agentium lock' first.\n")
        return 2

    try:
        baseline_lock = read_lock_file(lock_path)

        # Get current fingerprint
        target_str = args.from_target
        if not target_str and "source" in baseline_lock.metadata:
            target_str = baseline_lock.metadata["source"]

        if not target_str:
            sys.stderr.write(
                "Error: No fingerprint source specified. Provide --from <module:callable>.\n"
            )
            return 2

        fn = _load_target_callable(target_str)
        fp_kwargs = fn()
        current_fp = fingerprint(**fp_kwargs)

        report = diff_fingerprints(baseline_lock, current_fp)

        # Output format
        fmt = getattr(args, "format", "text")
        if getattr(args, "json", False) or fmt == "json":
            print(report.to_json())
        elif fmt == "md":
            print(report.to_markdown())
        else:
            print(report.to_text())

        return 1 if report.has_drift else 0
    except Exception as e:
        sys.stderr.write(f"Error running drift check: {e}\n")
        return 2


def create_parser() -> argparse.ArgumentParser:
    common_parent = argparse.ArgumentParser(add_help=False)
    common_parent.add_argument("--json", action="store_true", help="Format CLI output as JSON")

    parser = argparse.ArgumentParser(
        prog="agentium",
        description="Agentium v2 — Context & trust integrity toolkit for multi-agent and long-running AI agents.",
        parents=[common_parent],
    )
    parser.add_argument("--version", action="version", version="agentium 2.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # init (M2)
    p_init = subparsers.add_parser("init", parents=[common_parent], help="Initialize agentium.toml in the current project")
    p_init.add_argument("--dry-run", action="store_true", help="Print diff without modifying files")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing configuration")

    # doctor (M2)
    p_doc = subparsers.add_parser("doctor", parents=[common_parent], help="Inspect environment health, pins, and lineage status")
    p_doc.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    p_doc.add_argument("--with-scanners", action="store_true", help="Execute configured external scanners")
    p_doc.add_argument("--check-lock", action="store_true", help="Compare current fingerprint with lock file")
    p_doc.add_argument("--from", dest="from_target", help="Module:callable returning fingerprint target")

    # lock & check (M1)
    p_lock = subparsers.add_parser(
        "lock",
        parents=[common_parent],
        help="Record baseline model, prompt, and tool schema fingerprint. SECURITY NOTE: --from executes user code.",
    )
    p_lock.add_argument("--from", dest="from_target", required=True, help="Module:callable returning fingerprint target dict")

    p_check = subparsers.add_parser(
        "check",
        parents=[common_parent],
        help="Verify current agent components against agentium.lock. SECURITY NOTE: --from executes user code.",
    )
    p_check.add_argument("--from", dest="from_target", help="Module:callable returning current target dict")
    p_check.add_argument("--format", choices=["text", "json", "md"], default="text", help="Output format")

    # lineage (M4)
    p_lineage = subparsers.add_parser("lineage", parents=[common_parent], help="Query claim lineage and provenance graphs")
    lin_sub = p_lineage.add_subparsers(dest="lineage_command")
    p_claims = lin_sub.add_parser("claims", parents=[common_parent], help="List claims for a run")
    p_claims.add_argument("run_id", help="Run ID to inspect")
    p_claims.add_argument("--status", help="Filter by claim status")

    p_blame = lin_sub.add_parser("blame", parents=[common_parent], help="Produce blame report for a specific claim")
    p_blame.add_argument("run_id", help="Run ID")
    p_blame.add_argument("claim_id", help="Claim ID")

    p_diff = lin_sub.add_parser("diff", parents=[common_parent], help="Diff claims and handoff topology between two runs")
    p_diff.add_argument("run_a", help="First run ID")
    p_diff.add_argument("run_b", help="Second run ID")

    # handoff (M4)
    p_handoff = subparsers.add_parser("handoff", parents=[common_parent], help="Inspect and lint handoff packets")
    han_sub = p_handoff.add_subparsers(dest="handoff_command")
    p_hlint = han_sub.add_parser("lint", parents=[common_parent], help="Lint handoff packet file(s)")
    p_hlint.add_argument("target", help="File path or glob")

    # pins & soak (M3)
    p_pins = subparsers.add_parser("pins", parents=[common_parent], help="Inspect context pins")
    pins_sub = p_pins.add_subparsers(dest="pins_command")
    p_plist = pins_sub.add_parser("list", parents=[common_parent], help="List active pins")
    p_plist.add_argument("--run", help="Filter by run ID")
    pins_sub.add_parser("render", parents=[common_parent], help="Render deterministic pin text block")

    p_soak = subparsers.add_parser("soak", parents=[common_parent], help="Run compaction soak test")
    p_soak.add_argument("--config", help="Path to soak config TOML")

    return parser


def handle_init(args: argparse.Namespace) -> int:
    from .init_cmd import run_init
    project_root = Path.cwd()
    dry_run = getattr(args, "dry_run", False)
    force = getattr(args, "force", False)
    as_json = getattr(args, "json", False)

    code, msg = run_init(project_root, dry_run=dry_run, force=force, as_json=as_json)
    if code != 0 and not as_json:
        sys.stderr.write(msg)
    else:
        sys.stdout.write(msg)
    return code


def handle_doctor(args: argparse.Namespace) -> int:
    from .doctor_cmd import run_doctor
    project_root = Path.cwd()
    strict = getattr(args, "strict", False)
    check_lock = getattr(args, "check_lock", False)
    from_target = getattr(args, "from_target", None)
    as_json = getattr(args, "json", False)

    code, msg = run_doctor(
        project_root,
        strict=strict,
        check_lock=check_lock,
        from_target=from_target,
        as_json=as_json,
    )
    sys.stdout.write(msg)
    return code


def handle_pins(args: argparse.Namespace) -> int:
    from ..pin.store import PinStore
    from ..core.events import EventReader
    from ..core.config import load_config

    subcmd = getattr(args, "pins_command", None)
    cfg = load_config()

    if subcmd == "list":
        run_filter = getattr(args, "run", None)
        reader = EventReader(events_dir=cfg.core.events_dir)
        runs = [run_filter] if run_filter else reader.list_runs()
        found_pins = []
        for r_id in runs:
            for ev in reader.read_run(r_id):
                if ev.type == "pin":
                    found_pins.append({"run_id": r_id, **ev.payload})

        if getattr(args, "json", False):
            print(json.dumps(found_pins, indent=2))
        else:
            if not found_pins:
                print("No context pins found.")
            else:
                for p in found_pins:
                    print(f"[{p.get('run_id')}] pin:{p.get('key')} -> {p.get('text')}")
        return 0

    elif subcmd == "render":
        # Render pins from latest active run or empty store
        store = PinStore()
        rendered = store.render()
        if getattr(args, "json", False):
            print(json.dumps({"rendered": rendered}))
        else:
            print(rendered if rendered else "(No active pins)")
        return 0

    print("Use 'agentium pins list' or 'agentium pins render'.")
    return 0


def handle_soak(args: argparse.Namespace) -> int:
    from ..pin.soak import soak

    report = soak(num_turns=20, pin_interval=3, compaction_threshold=8)
    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.to_text())
    return 0 if report.all_passed else 1


def handle_lineage(args: argparse.Namespace) -> int:
    from ..core.events import EventReader
    from ..core.config import load_config
    from ..lineage.graph import LineageGraph, diff_lineage

    cfg = load_config()
    reader = EventReader(events_dir=cfg.core.events_dir)
    subcmd = getattr(args, "lineage_command", None)

    if subcmd == "claims":
        run_id = args.run_id
        events = reader.read_run(run_id)
        claims = []
        for ev in events:
            if ev.type == "claim":
                cdata = ev.payload.get("claim", {})
                if args.status:
                    if cdata.get("status") == args.status:
                        claims.append(cdata)
                else:
                    claims.append(cdata)

        if getattr(args, "json", False):
            print(json.dumps(claims, indent=2))
        else:
            if not claims:
                print(f"No claims found for run '{run_id}'.")
            else:
                for c in claims:
                    print(f"[{c.get('status', 'unverified').upper()}] {c.get('id')}: {c.get('statement')}")
        return 0

    elif subcmd == "blame":
        run_id = args.run_id
        claim_id = args.claim_id
        events = reader.read_run(run_id)
        graph = LineageGraph.from_events(events, run_id=run_id)
        try:
            report = graph.blame(claim_id)
            if getattr(args, "json", False):
                print(json.dumps(report.to_dict(), indent=2))
            else:
                print(report.to_text())
            return 0
        except KeyError as e:
            sys.stderr.write(f"Error: {e}\n")
            return 1

    elif subcmd == "diff":
        run_a = args.run_a
        run_b = args.run_b
        graph_a = LineageGraph.from_events(reader.read_run(run_a), run_id=run_a)
        graph_b = LineageGraph.from_events(reader.read_run(run_b), run_id=run_b)
        ldiff = diff_lineage(graph_a, graph_b)
        if getattr(args, "json", False):
            print(json.dumps(ldiff.to_dict(), indent=2))
        else:
            print(ldiff.to_text())
        return 0

    print("Use 'agentium lineage claims', 'agentium lineage blame', or 'agentium lineage diff'.")
    return 0


def handle_handoff(args: argparse.Namespace) -> int:
    from ..lineage.handoff import HandoffPacket, lint_handoff

    subcmd = getattr(args, "handoff_command", None)
    if subcmd == "lint":
        target = Path(args.target)
        if not target.is_file():
            sys.stderr.write(f"Error: Target file not found: {target}\n")
            return 2

        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            packet = HandoffPacket.from_dict(data)
            issues = lint_handoff(packet)

            if getattr(args, "json", False):
                print(json.dumps([i.to_dict() for i in issues], indent=2))
            else:
                if not issues:
                    print(f"Handoff packet '{target.name}': No issues found.")
                else:
                    print(f"Lint issues for '{target.name}':")
                    for iss in issues:
                        print(f"  [{iss.severity}] {iss.code}: {iss.message}")

            has_errors = any(i.severity == "ERROR" for i in issues)
            return 1 if has_errors else 0
        except Exception as e:
            sys.stderr.write(f"Error parsing handoff packet: {e}\n")
            return 2

    print("Use 'agentium handoff lint <path>'.")
    return 0


def main(args: Optional[List[str]] = None) -> int:
    parser = create_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    if parsed.command == "lock":
        return handle_lock(parsed)
    elif parsed.command == "check":
        return handle_check(parsed)
    elif parsed.command == "init":
        return handle_init(parsed)
    elif parsed.command == "doctor":
        return handle_doctor(parsed)
    elif parsed.command == "pins":
        return handle_pins(parsed)
    elif parsed.command == "soak":
        return handle_soak(parsed)
    elif parsed.command == "lineage":
        return handle_lineage(parsed)
    elif parsed.command == "handoff":
        return handle_handoff(parsed)

    if getattr(parsed, "json", False):
        print(json.dumps({"command": parsed.command, "status": "ok"}))
    else:
        print(f"Agentium CLI: command '{parsed.command}' (to be implemented in respective milestone)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
