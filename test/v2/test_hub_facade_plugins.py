"""Tests for Agentium Facade (agentium.use) and Plugin Discovery (agentium.plugins)."""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import agentium
from agentium.hub.facade import use
from agentium.hub.plugins import discover_plugins, get_plugin, list_plugins, register_plugin


def test_facade_jmespath():
    adapter = use("jmespath")
    assert hasattr(adapter, "search"), "jmespath adapter must export search"
    assert hasattr(adapter, "compile"), "jmespath adapter must export compile"
    # Execute a search using installed jmespath
    res = adapter.search("foo.bar", {"foo": {"bar": 42}})
    assert res == 42
    print("[PASS] test_facade_jmespath passed.")


def test_facade_missing_extra_error_message():
    try:
        use("non_existent_extra_xyz")
        assert False, "Expected ImportError"
    except ImportError as exc:
        msg = str(exc)
        assert "agentium[non_existent_extra_xyz]" in msg, f"Error message should mention pip install: {msg}"
    print("[PASS] test_facade_missing_extra_error_message passed.")


def test_facade_lazy_adapter_error_message():
    # cachetools or tenacity may not be installed; test calling without dependency
    adapter = use("cachetools")
    assert hasattr(adapter, "ttl_cache")
    try:
        # If cachetools is not installed, it should raise informative error
        import cachetools  # noqa
        print("[INFO] cachetools is installed in environment, testing normal call")
        @adapter.ttl_cache(maxsize=10, ttl=60)
        def sample(x):
            return x * 2
        assert sample(5) == 10
    except ImportError:
        # If not installed, invoking it must raise ImportError with pip install hint
        try:
            @adapter.ttl_cache(maxsize=10, ttl=60)
            def sample2(x):
                return x * 2
            sample2(5)
            assert False, "Expected ImportError when extra not installed"
        except ImportError as exc:
            assert "pip install" in str(exc)
            assert "cachetools" in str(exc)
            print("[PASS] Informative ImportError raised for missing cachetools.")
    print("[PASS] test_facade_lazy_adapter_error_message passed.")


def test_plugin_discovery_and_registration():
    # Discovery does not fail in clean environment
    discovered = discover_plugins()
    assert isinstance(discovered, dict)

    # In-memory registration
    class SamplePlugin:
        name = "test_plugin"
        def execute(self):
            return "ok"

    plugin_instance = SamplePlugin()
    register_plugin("sample_in_memory", plugin_instance)

    retrieved = get_plugin("sample_in_memory")
    assert retrieved is plugin_instance
    assert retrieved.execute() == "ok"

    all_plugs = list_plugins()
    assert "sample_in_memory" in all_plugs
    print("[PASS] test_plugin_discovery_and_registration passed.")


if __name__ == "__main__":
    test_facade_jmespath()
    test_facade_missing_extra_error_message()
    test_facade_lazy_adapter_error_message()
    test_plugin_discovery_and_registration()
    print("\nALL HUB FACADE AND PLUGIN TESTS PASSED!")
