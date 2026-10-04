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
from agentium.core.events import EventReader, EventType


def test_basic_run_context_and_events():
    print("Testing basic run context and events...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = agentium.load_config()
        cfg.core.events_dir = tmp_dir

        with agentium.run(name="test-run", agent_id="agent-007", config=cfg) as active_run:
            assert agentium.get_current_run() is active_run
            assert active_run.run_id is not None
            active_run.log("tool_call", {"tool": "weather", "city": "London"})

        assert agentium.get_current_run() is None

        # Verify events logged
        reader = EventReader(run_id=active_run.run_id, events_dir=tmp_dir)
        events = reader.read_all()
        types = [e.type for e in events]
        assert types == ["run_start", "tool_call", "run_end"]
        print("[PASS] Basic run context and event sequence OK")


def test_async_and_nested_inheritance():
    print("Testing async and nested run context inheritance...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = agentium.load_config()
        cfg.core.events_dir = tmp_dir

        async def sub_task():
            current = agentium.get_current_run()
            assert current is not None
            assert current.name == "parent-run"
            current.log("llm_call", {"prompt": "hello"})

        async def main_async():
            with agentium.run(name="parent-run", config=cfg) as pr:
                await asyncio.gather(sub_task(), sub_task())
            return pr.run_id

        run_id = asyncio.run(main_async())

        reader = EventReader(run_id=run_id, events_dir=tmp_dir)
        events = reader.read_all()
        assert len(events) == 4  # run_start, 2 llm_calls, run_end
        print("[PASS] Async and nested contextvars inheritance OK")


def test_exception_handling_in_run():
    print("Testing exception logging in run context...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = agentium.load_config()
        cfg.core.events_dir = tmp_dir

        run_id = None
        try:
            with agentium.run(name="failing-run", config=cfg) as fr:
                run_id = fr.run_id
                raise RuntimeError("Simulated crash")
        except RuntimeError:
            pass

        assert run_id is not None
        reader = EventReader(run_id=run_id, events_dir=tmp_dir)
        events = reader.read_all()
        types = [e.type for e in events]
        assert types == ["run_start", "error", "run_end"]
        error_ev = [e for e in events if e.type == "error"][0]
        assert "Simulated crash" in error_ev.payload["exception"]
        print("[PASS] Exception logged with error event OK")


if __name__ == "__main__":
    test_basic_run_context_and_events()
    test_async_and_nested_inheritance()
    test_exception_handling_in_run()
    print("\nALL RUN CONTEXT TESTS PASSED!")
