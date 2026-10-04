import json
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agentium.core.events import Event, EventReader, EventType, EventWriter


def test_event_serialization_and_unknown_fields():
    print("Testing Event serialization and forward compatibility...")
    ev = Event(
        schema_version=1,
        run_id="run-123",
        event_id=1,
        type=EventType.RUN_START.value,
        payload={"task": "inspect", "future_field_xyz": 42},
    )
    d = ev.to_dict()
    # Add unknown top-level field to test forward compatibility
    d["future_extra_field"] = "unexpected_future_data"
    d["another_version_flag"] = 99

    ev_reconstructed = Event.from_dict(d)
    assert ev_reconstructed.run_id == "run-123"
    assert ev_reconstructed.event_id == 1
    assert ev_reconstructed.payload["future_field_xyz"] == 42
    print("[PASS] Event serialization & forward compatibility OK")


def test_thread_safe_writer_and_reader():
    print("Testing thread-safe writer and reader...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        writer = EventWriter(run_id="run-threads", events_dir=tmp_dir)

        def worker(idx: int):
            for i in range(10):
                writer.write(EventType.TOOL_CALL, {"worker": idx, "seq": i})

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        reader = EventReader(run_id="run-threads", events_dir=tmp_dir)
        events = reader.read_all()
        assert len(events) == 50, f"Expected 50 events, found {len(events)}"
        # Verify event_ids are monotonic
        event_ids = [e.event_id for e in events]
        assert sorted(event_ids) == list(range(1, 51))
        print("[PASS] Thread-safe writer with 50 concurrent events OK")


def test_multi_process_file_merging():
    print("Testing multi-process file merging...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Simulate two different processes writing to <run_id>.<pid>.jsonl
        file_pid1 = Path(tmp_dir) / "run-multi.1001.jsonl"
        file_pid2 = Path(tmp_dir) / "run-multi.1002.jsonl"

        ev1 = Event(run_id="run-multi", event_id=1, ts="2026-10-04T10:00:00Z", type="run_start", payload={})
        ev2 = Event(run_id="run-multi", event_id=2, ts="2026-10-04T10:00:01Z", type="tool_call", payload={"p": 1})
        ev3 = Event(run_id="run-multi", event_id=1, ts="2026-10-04T10:00:02Z", type="tool_call", payload={"p": 2})

        with open(file_pid1, "w", encoding="utf-8") as f:
            f.write(ev1.to_json() + "\n")
            f.write(ev2.to_json() + "\n")

        with open(file_pid2, "w", encoding="utf-8") as f:
            f.write(ev3.to_json() + "\n")

        reader = EventReader(run_id="run-multi", events_dir=tmp_dir)
        merged = reader.read_all()
        assert len(merged) == 3
        # Sorted by ts
        assert [e.ts for e in merged] == [
            "2026-10-04T10:00:00Z",
            "2026-10-04T10:00:01Z",
            "2026-10-04T10:00:02Z",
        ]
        print("[PASS] Multi-process log file merge OK")


def test_truncated_line_tolerance():
    print("Testing truncated line tolerance...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "run-trunc.jsonl"
        ev = Event(run_id="run-trunc", event_id=1, type="run_start", payload={"ok": True})
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(ev.to_json() + "\n")
            # Write a partial/corrupted trailing line
            f.write('{"schema_version": 1, "run_id": "run-trunc", "event_id": 2, "pa\n')

        reader = EventReader(run_id="run-trunc", events_dir=tmp_dir)
        events = reader.read_all()
        assert len(events) == 1
        assert events[0].event_id == 1
        print("[PASS] Truncated line tolerated without exception OK")


def test_writer_never_raises():
    print("Testing writer never raises on filesystem failure...")
    # Point to an invalid directory or read-only simulation
    # Using a filename as events_dir so mkdir fails
    with tempfile.NamedTemporaryFile() as tmp_file:
        bad_dir = tmp_file.name
        writer = EventWriter(run_id="run-fail", events_dir=bad_dir)
        # Should not raise exception
        result = writer.write(EventType.RUN_START, {"test": True})
        assert result is None
    print("[PASS] Writer non-raising guarantee OK")


if __name__ == "__main__":
    test_event_serialization_and_unknown_fields()
    test_thread_safe_writer_and_reader()
    test_multi_process_file_merging()
    test_truncated_line_tolerance()
    test_writer_never_raises()
    print("\nALL EVENTS TESTS PASSED!")
