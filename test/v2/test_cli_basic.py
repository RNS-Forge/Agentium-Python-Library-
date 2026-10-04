import io
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agentium.cli.main import main


def test_cli_help_and_version():
    print("Testing CLI help and version...")

    # Test --version (raises SystemExit(0))
    try:
        main(["--version"])
        assert False, "Expected SystemExit on --version"
    except SystemExit as e:
        assert e.code == 0

    # Test --help (raises SystemExit(0))
    try:
        main(["--help"])
        assert False, "Expected SystemExit on --help"
    except SystemExit as e:
        assert e.code == 0

    print("[PASS] CLI help and version OK")


def test_cli_subcommands_and_json():
    print("Testing CLI subcommands with --json...")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        old_cwd = os.getcwd()
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            os.chdir(tmp_dir)
            code = main(["init", "--json"])
            output = sys.stdout.getvalue()
            assert code == 0, f"Expected code 0, got {code}: {output}"
            data = json.loads(output)
            assert data["status"] == "ok"
            assert "file" in data
        finally:
            os.chdir(old_cwd)
            sys.stdout = old_stdout

    print("[PASS] CLI subcommands with --json OK")


if __name__ == "__main__":
    test_cli_help_and_version()
    test_cli_subcommands_and_json()
    print("\nALL BASIC CLI TESTS PASSED!")
