import asyncio
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import agentium
from agentium.adapters.plain import get_tool_registry
from agentium.core.events import EventReader


def test_tool_registration_and_effects():
    print("Testing tool registration and effect tags...")

    @agentium.tool(effect="read")
    def fetch_data(x: int) -> int:
        """Fetch some integer data."""
        return x * 2

    @agentium.tool(name="delete_account", effect="destructive")
    def purge(user_id: str) -> bool:
        return True

    registry = get_tool_registry()
    assert registry.get_effect("fetch_data") == "read"
    assert registry.get_effect("delete_account") == "destructive"
    assert registry.get("fetch_data").doc == "Fetch some integer data."

    # Invalid effect rejection
    try:
        @agentium.tool(effect="magic_unknown_effect")
        def invalid_fn():
            pass

        assert False, "Expected ValueError on invalid effect"
    except ValueError:
        pass

    print("[PASS] Tool registration & effect validation OK")


def test_tool_execution_in_run():
    print("Testing tool execution and logging inside run context...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = agentium.load_config()
        cfg.core.events_dir = tmp_dir

        @agentium.tool(effect="write")
        def update_record(rec_id: int, val: str) -> dict:
            return {"status": "updated", "id": rec_id, "val": val}

        @agentium.tool(effect="read")
        async def fetch_async(url: str) -> str:
            await asyncio.sleep(0.01)
            return f"content_of_{url}"

        with agentium.run(name="tool-runner", config=cfg) as active_run:
            # 1. Sync tool call
            res1 = update_record(42, "agentium-v2")
            assert res1 == {"status": "updated", "id": 42, "val": "agentium-v2"}

            # 2. Async tool call
            res2 = asyncio.run(fetch_async("https://example.com"))
            assert res2 == "content_of_https://example.com"

        reader = EventReader(run_id=active_run.run_id, events_dir=tmp_dir)
        events = reader.read_all()
        types = [e.type for e in events]
        assert types == [
            "run_start",
            "tool_call",
            "tool_result",
            "tool_call",
            "tool_result",
            "run_end",
        ]

        # Verify tool_result contains duration_ms and result
        res_event = events[2]
        assert res_event.type == "tool_result"
        assert res_event.payload["tool"] == "update_record"
        assert res_event.payload["success"] is True
        assert res_event.payload["duration_ms"] >= 0.0
        assert res_event.payload["result"] == {"status": "updated", "id": 42, "val": "agentium-v2"}

        print("[PASS] Tool execution and event logging OK")


def test_tool_exception_passthrough():
    print("Testing tool exception pass-through and failure logging...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = agentium.load_config()
        cfg.core.events_dir = tmp_dir

        @agentium.tool(effect="destructive")
        def exploding_tool():
            raise ZeroDivisionError("division by zero in tool")

        with agentium.run(name="exploding-run", config=cfg) as active_run:
            try:
                exploding_tool()
                assert False, "Should have raised ZeroDivisionError"
            except ZeroDivisionError:
                pass

        reader = EventReader(run_id=active_run.run_id, events_dir=tmp_dir)
        events = reader.read_all()
        result_ev = [e for e in events if e.type == "tool_result"][0]
        assert result_ev.payload["success"] is False
        assert "division by zero in tool" in result_ev.payload["error"]
        print("[PASS] Tool exception pass-through OK")


if __name__ == "__main__":
    test_tool_registration_and_effects()
    test_tool_execution_in_run()
    test_tool_exception_passthrough()
    print("\nALL TOOL DECORATOR TESTS PASSED!")
