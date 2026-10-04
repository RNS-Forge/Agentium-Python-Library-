from __future__ import annotations

import contextvars
import uuid
from typing import Any, Dict, Optional, Union

from .config import AgentiumConfig, load_config
from .events import Event, EventType, EventWriter
from .redact import Redactor, get_default_redactor

_current_run_ctx: contextvars.ContextVar[Optional["RunContext"]] = contextvars.ContextVar(
    "current_run_ctx", default=None
)


def get_current_run() -> Optional["RunContext"]:
    """Retrieve the active RunContext for the current execution context."""
    return _current_run_ctx.get()


class RunContext:
    """Active execution run context providing event logging and metadata."""

    def __init__(
        self,
        name: str = "default",
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        config: Optional[AgentiumConfig] = None,
        parent_run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.agent_id = agent_id
        self.run_id = run_id or str(uuid.uuid4())
        self.config = config or load_config()
        self.parent_run_id = parent_run_id
        self.metadata = metadata or {}

        redactor = get_default_redactor() if self.config.core.redaction else None
        self.writer = EventWriter(
            run_id=self.run_id,
            events_dir=self.config.core.events_dir,
            flush_per_event=self.config.core.flush_per_event,
            redactor=redactor,
        )
        self._token: Optional[contextvars.Token] = None

    @property
    def event_writer(self) -> EventWriter:
        """Alias for self.writer."""
        return self.writer

    def log(
        self,
        event_type: Union[EventType, str],
        payload: Dict[str, Any],
        agent_id: Optional[str] = None,
        parent_id: Optional[int] = None,
    ) -> Optional[Event]:
        """Log an event directly into this run's JSONL log."""
        eff_agent = agent_id or self.agent_id
        return self.writer.write(event_type, payload, agent_id=eff_agent, parent_id=parent_id)

    def __enter__(self) -> "RunContext":
        parent = get_current_run()
        if parent is not None and not self.parent_run_id:
            self.parent_run_id = parent.run_id

        self._token = _current_run_ctx.set(self)
        self.log(
            EventType.RUN_START,
            {
                "name": self.name,
                "agent_id": self.agent_id,
                "parent_run_id": self.parent_run_id,
                "metadata": self.metadata,
            },
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            if exc_val is not None:
                self.log(
                    EventType.ERROR,
                    {
                        "exception_type": str(exc_type),
                        "exception": str(exc_val),
                    },
                )
            self.log(
                EventType.RUN_END,
                {
                    "name": self.name,
                    "success": exc_val is None,
                },
            )
        finally:
            if self._token is not None:
                _current_run_ctx.reset(self._token)


def run(
    name: str = "default",
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None,
    config: Optional[AgentiumConfig] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> RunContext:
    """Create a new Agentium run context."""
    return RunContext(name=name, agent_id=agent_id, run_id=run_id, config=config, metadata=metadata)
