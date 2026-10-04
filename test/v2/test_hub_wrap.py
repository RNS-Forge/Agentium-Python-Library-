"""Tests for Agentium Universal Wrapper (agentium.wrap, agentium.wrap_async)."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import agentium
from agentium.core.events import EventType
from agentium.hub.wrapper import wrap, wrap_async


def test_sync_wrap_basic():
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    wrapped_add = wrap(add, effect="read", name="custom_add")
    assert hasattr(wrapped_add, "raw"), "Wrapped tool must expose .raw"
    assert wrapped_add.raw is add
    assert wrapped_add.__agentium_tool_effect__ == "read"
    assert getattr(wrapped_add, "__name__") == "custom_add"

    # Call wrapped tool and check return value
    result = wrapped_add(10, 20)
    assert result == 30, f"Expected 30, got {result}"
    print("[PASS] test_sync_wrap_basic passed.")


def test_sync_wrap_events():
    def compute_sqrt(x: float) -> float:
        return x ** 0.5

    wrapped = wrap(compute_sqrt, effect="read", name="sqrt_tool")

    with agentium.run() as ctx:
        res = wrapped(16.0)
        assert res == 4.0

    # Verify events recorded
    reader = agentium.EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    tool_calls = [e for e in events if e.type == EventType.TOOL_CALL.value]
    tool_results = [e for e in events if e.type == EventType.TOOL_RESULT.value]

    assert len(tool_calls) == 1, f"Expected 1 tool_call event, got {len(tool_calls)}"
    assert len(tool_results) == 1, f"Expected 1 tool_result event, got {len(tool_results)}"
    assert tool_calls[0].payload["tool_name"] == "sqrt_tool"
    assert tool_calls[0].payload["effect"] == "read"
    assert tool_results[0].payload["status"] == "success"
    print("[PASS] test_sync_wrap_events passed.")


def test_sync_wrap_exception_transparency():
    def failing_tool():
        raise ValueError("Invalid parameter value!")

    wrapped = wrap(failing_tool, effect="destructive", name="failer")

    with agentium.run() as ctx:
        try:
            wrapped()
            assert False, "Expected ValueError"
        except ValueError as err:
            assert str(err) == "Invalid parameter value!"

    # Error status in tool_result event was recorded
    reader = agentium.EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    results = [e for e in events if e.type == EventType.TOOL_RESULT.value]
    assert len(results) == 1, "Failed tool call must emit TOOL_RESULT event"
    assert results[0].payload["status"] == "error"
    assert results[0].payload["error"] == "ValueError"
    print("[PASS] test_sync_wrap_exception_transparency passed.")


def test_async_wrap_basic_and_events():
    async def async_fetch_data(user_id: str) -> dict:
        await asyncio.sleep(0.01)
        return {"id": user_id, "status": "active"}

    wrapped = wrap_async(async_fetch_data, effect="read", name="fetch_user")
    assert hasattr(wrapped, "raw")
    assert wrapped.raw is async_fetch_data
    assert wrapped.__agentium_tool_effect__ == "read"

    async def _run():
        with agentium.run() as ctx:
            data = await wrapped("user_42")
            assert data == {"id": "user_42", "status": "active"}

            reader = agentium.EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
            events = list(reader)
            tool_calls = [e for e in events if e.type == EventType.TOOL_CALL.value]
            tool_results = [e for e in events if e.type == EventType.TOOL_RESULT.value]
            assert len(tool_calls) == 1
            assert len(tool_results) == 1
            assert tool_results[0].payload["status"] == "success"

    asyncio.run(_run())
    print("[PASS] test_async_wrap_basic_and_events passed.")


def test_object_wrapper():
    class DummyClient:
        def __init__(self):
            self.value = 100

        def query(self, q: str) -> str:
            return f"Answer for {q}"

    client = DummyClient()
    wrapped_client = wrap(client, name="dummy_service")
    assert hasattr(wrapped_client, "raw")
    assert wrapped_client.raw is client
    assert wrapped_client.value == 100

    with agentium.run() as ctx:
        res = wrapped_client.query("status")
        assert res == "Answer for status"

    reader = agentium.EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    tool_calls = [e for e in events if e.type == EventType.TOOL_CALL.value]
    assert len(tool_calls) == 1
    assert tool_calls[0].payload["tool_name"] == "dummy_service.query"

    print("[PASS] test_object_wrapper passed.")


if __name__ == "__main__":
    test_sync_wrap_basic()
    test_sync_wrap_events()
    test_sync_wrap_exception_transparency()
    test_async_wrap_basic_and_events()
    test_object_wrapper()
    print("\nALL UNIVERSAL WRAPPER TESTS PASSED!")
