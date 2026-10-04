import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agentium.core.config import AgentiumConfig, find_config_file, load_config


def test_default_config():
    print("Testing default configuration values...")
    cfg = load_config(config_path=Path("non_existent_path.toml"))
    assert cfg.core.events_dir == ".agentium/events"
    assert cfg.core.flush_per_event is True
    assert cfg.gate.mode == "enforce"
    assert cfg.handoff.max_tokens == 2000
    assert cfg.pin.reinject_position == "end"
    print("[PASS] Default configuration values OK")


def test_toml_file_loading():
    print("Testing TOML file loading via tomllib...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_content = """
[core]
events_dir = "custom/events"
flush_per_event = false

[lineage]
trusted_tools = ["db_read", "search_api"]

[gate]
mode = "shadow"
on_destructive_undeclared = "block"

[handoff]
max_tokens = 3500
on_overflow = "truncate_unverified"

[pin]
reinject_position = "start"

[prefetch]
enabled = true
max_in_flight = 5
"""
        config_path = Path(tmp_dir) / "agentium.toml"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(toml_content)

        cfg = load_config(config_path=config_path)
        assert cfg.core.events_dir == "custom/events"
        assert cfg.core.flush_per_event is False
        assert cfg.lineage.trusted_tools == ["db_read", "search_api"]
        assert cfg.gate.mode == "shadow"
        assert cfg.gate.on_destructive_undeclared == "block"
        assert cfg.handoff.max_tokens == 3500
        assert cfg.handoff.on_overflow == "truncate_unverified"
        assert cfg.pin.reinject_position == "start"
        assert cfg.prefetch.enabled is True
        assert cfg.prefetch.max_in_flight == 5
        print("[PASS] TOML file parsing via stdlib tomllib OK")


def test_env_var_overrides():
    print("Testing AGENTIUM_* environment variable overrides...")
    os.environ["AGENTIUM_CORE_EVENTS_DIR"] = "env/overridden/events"
    os.environ["AGENTIUM_GATE_MODE"] = "shadow"
    os.environ["AGENTIUM_HANDOFF_MAX_TOKENS"] = "4000"

    try:
        cfg = load_config(config_path=Path("non_existent.toml"))
        assert cfg.core.events_dir == "env/overridden/events"
        assert cfg.gate.mode == "shadow"
        assert cfg.handoff.max_tokens == 4000
        print("[PASS] Environment variable overrides OK")
    finally:
        del os.environ["AGENTIUM_CORE_EVENTS_DIR"]
        del os.environ["AGENTIUM_GATE_MODE"]
        del os.environ["AGENTIUM_HANDOFF_MAX_TOKENS"]


def test_upward_search():
    print("Testing upward directory search for agentium.toml...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        parent_dir = Path(tmp_dir).resolve()
        nested_dir = parent_dir / "subdir" / "nested"
        nested_dir.mkdir(parents=True)

        config_path = parent_dir / "agentium.toml"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write('[gate]\nmode = "shadow"\n')

        found = find_config_file(start_dir=nested_dir)
        assert found is not None
        assert found.resolve() == config_path.resolve()
        print("[PASS] Upward search for agentium.toml OK")


if __name__ == "__main__":
    test_default_config()
    test_toml_file_loading()
    test_env_var_overrides()
    test_upward_search()
    print("\nALL CONFIG TESTS PASSED!")
