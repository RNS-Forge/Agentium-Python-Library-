import os
import subprocess
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_suite():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = [
        "test_events.py",
        "test_canonical_hashing.py",
        "test_redaction.py",
        "test_run_context.py",
        "test_tool_decorator.py",
        "test_config.py",
        "test_zero_deps.py",
        "test_otel.py",
        "test_cli_basic.py",
        "test_v1_backward_compat.py",
    ]

    print("=" * 65)
    print("RUNNING AGENTIUM V2 MILESTONE 0 (FOUNDATION) TEST SUITE")
    print("=" * 65)

    results = {}
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    for tf in test_files:
        path = os.path.join(test_dir, tf)
        if not os.path.exists(path):
            continue
        print(f"\n>> Executing {tf}...")
        proc = subprocess.run([sys.executable, path], capture_output=True, text=True, env=env)
        if proc.returncode == 0:
            print(f"[PASS] {tf}")
            results[tf] = "PASSED"
        else:
            print(f"[FAIL] {tf}")
            print(proc.stdout)
            print(proc.stderr)
            results[tf] = "FAILED"

    print("\n" + "=" * 65)
    print("MILESTONE 0 (M0) TEST REPORT SUMMARY")
    print("=" * 65)
    passed_count = sum(1 for status in results.values() if status == "PASSED")
    for tf, status in results.items():
        flag = "[PASS]" if status == "PASSED" else "[FAIL]"
        print(f"{flag} {tf:32} : {status}")
    print(f"\nTotal: {passed_count}/{len(results)} tests passed.")
    print("=" * 65)
    return passed_count == len(results)


if __name__ == "__main__":
    success = run_suite()
    sys.exit(0 if success else 1)
