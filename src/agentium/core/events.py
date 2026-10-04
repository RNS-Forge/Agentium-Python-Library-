from __future__ import annotations

import glob
import json
import logging
import os
import threading
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

logger = logging.getLogger("agentium.core.events")


class EventType(str, Enum):
    RUN_START = "run_start"
    RUN_END = "run_end"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CLAIM = "claim"
    CLAIM_CREATED = "claim_created"
    CLAIM_VERIFIED = "claim_verified"
    CLAIM_REFUTED = "claim_refuted"
    HANDOFF = "handoff"
    GATE_DECISION = "gate_decision"
    ACTION_GATE_BLOCK = "action_gate_block"
    ACTION_GATE_SHADOW_BLOCK = "action_gate_shadow_block"
    PIN_ADDED = "pin_added"
    PIN_SUPERSEDED = "pin_superseded"
    COMPACTION = "compaction"
    PIN_REINJECTED = "pin_reinjected"
    FINGERPRINT = "fingerprint"
    PREFETCH_ATTEMPT = "prefetch_attempt"
    PREFETCH_RESULT = "prefetch_result"
    ERROR = "error"


@dataclass(frozen=True)
class Event:
    schema_version: int = 1
    run_id: str = ""
    event_id: int = 0
    parent_id: Optional[int] = None
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    type: str = EventType.RUN_START.value
    agent_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    redacted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def event_type(self) -> str:
        return self.type

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        # Forward compatibility: accept unknown fields gracefully
        known_keys = {
            "schema_version",
            "run_id",
            "event_id",
            "parent_id",
            "ts",
            "type",
            "agent_id",
            "payload",
            "redacted",
        }
        filtered = {k: v for k, v in data.items() if k in known_keys}
        if "schema_version" not in filtered:
            filtered["schema_version"] = 1
        if "payload" not in filtered or not isinstance(filtered["payload"], dict):
            filtered["payload"] = {}
        return cls(**filtered)


class EventWriter:
    """Thread-safe, append-only, non-raising event log writer."""

    def __init__(
        self,
        run_id: str,
        events_dir: Union[str, Path] = ".agentium/events",
        flush_per_event: bool = True,
        redactor: Optional[Any] = None,
    ) -> None:
        self.run_id = run_id
        self.events_dir = Path(events_dir)
        self.flush_per_event = flush_per_event
        self.redactor = redactor
        self._lock = threading.Lock()
        self._event_counter = 0
        self._warned_error = False

        pid = os.getpid()
        self.file_path = self.events_dir / f"{run_id}.{pid}.jsonl"

    def _ensure_dir(self) -> None:
        self.events_dir.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        event_type: Union[EventType, str],
        payload: Dict[str, Any],
        agent_id: Optional[str] = None,
        parent_id: Optional[int] = None,
    ) -> Optional[Event]:
        """Write an event. Guaranteed never to raise into caller code."""
        with self._lock:
            try:
                self._event_counter += 1
                type_str = event_type.value if isinstance(event_type, EventType) else str(event_type)

                redacted = False
                payload_to_write = payload
                if self.redactor is not None:
                    try:
                        payload_to_write, was_redacted = self.redactor(payload)
                        redacted = was_redacted
                    except Exception as red_err:
                        logger.warning("Redaction failed, proceeding with original payload: %s", red_err)

                event = Event(
                    schema_version=1,
                    run_id=self.run_id,
                    event_id=self._event_counter,
                    parent_id=parent_id,
                    ts=datetime.now(timezone.utc).isoformat(),
                    type=type_str,
                    agent_id=agent_id,
                    payload=payload_to_write,
                    redacted=redacted,
                )

                self._ensure_dir()
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write(event.to_json() + "\n")
                    if self.flush_per_event:
                        f.flush()

                return event
            except Exception as e:
                if not self._warned_error:
                    self._warned_error = True
                    warnings.warn(f"Agentium EventWriter failed to write event: {e}", UserWarning, stacklevel=2)
                    logger.error("Event write failure for run %s: %s", self.run_id, e)
                return None


class EventReader:
    """Reader for run event logs with multi-process merging and corruption tolerance."""

    def __init__(self, run_id: Optional[str] = None, events_dir: Union[str, Path] = ".agentium/events") -> None:
        self.run_id = run_id
        self.events_dir = Path(events_dir)

    @classmethod
    def list_runs(cls, events_dir: Union[str, Path] = ".agentium/events") -> List[str]:
        """List distinct run_ids discovered in events directory."""
        dir_path = Path(events_dir)
        if not dir_path.is_dir():
            return []
        run_ids = set()
        for f in dir_path.glob("*.jsonl"):
            parts = f.name.split(".")
            if len(parts) >= 2 and parts[-1] == "jsonl":
                run_ids.add(parts[0])
        return sorted(list(run_ids), reverse=True)

    def get_event_files(self) -> List[Path]:
        if self.run_id:
            pattern = str(self.events_dir / f"{self.run_id}*.jsonl")
        else:
            pattern = str(self.events_dir / "*.jsonl")
        return [Path(p) for p in glob.glob(pattern)]

    def read_run(self, run_id: str) -> List[Event]:
        reader = EventReader(run_id=run_id, events_dir=self.events_dir)
        return reader.read_all()

    def read_all(self) -> List[Event]:
        events: List[Event] = []
        for file_path in self.get_event_files():
            if not file_path.is_file():
                continue
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if isinstance(data, dict):
                            events.append(Event.from_dict(data))
                    except json.JSONDecodeError:
                        # Tolerate truncated final line or corruption
                        continue

        # Deterministic sort: timestamp then event_id
        events.sort(key=lambda ev: (ev.ts, ev.event_id))
        return events

    def __iter__(self) -> Iterator[Event]:
        return iter(self.read_all())
