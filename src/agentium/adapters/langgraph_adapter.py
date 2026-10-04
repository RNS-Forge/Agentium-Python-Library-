"""LangGraph Framework Adapter for Agentium v2.

Integrates Agentium run context, event tracing, pin re-injection,
and action gating with LangGraph state graphs.
"""
from __future__ import annotations

import copy
import functools
from typing import Any, Callable, Dict, List, Optional

from ..core.events import EventType, EventWriter
from ..core.run import get_current_run
from ..pin.guard import reinject
from ..pin.store import PinStore


def _check_langgraph_installed() -> None:
    try:
        import langgraph  # type: ignore # noqa: F401
    except ImportError as e:
        raise ImportError(
            "LangGraph adapter requires 'langgraph'. "
            "Install it via: pip install 'agentium[langgraph]'"
        ) from e


class LangGraphAdapter:
    """Adapter bridging LangGraph node execution and checkpoints to Agentium."""

    def __init__(
        self,
        pin_store: Optional[PinStore] = None,
        event_writer: Optional[EventWriter] = None,
        enforce_pins: bool = True,
    ) -> None:
        self.pin_store = pin_store or PinStore()
        self.event_writer = event_writer
        self.enforce_pins = enforce_pins

    def _get_writer(self) -> Optional[EventWriter]:
        if self.event_writer is not None:
            return self.event_writer
        ctx = get_current_run()
        return ctx.event_writer if ctx is not None else None

    def wrap_node(self, node_name: str, fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """Wrap a LangGraph node function to trace execution and preserve pins in messages."""
        @functools.wraps(fn)
        def wrapped_node(state: Dict[str, Any]) -> Dict[str, Any]:
            writer = self._get_writer()
            if writer:
                writer.write(
                    EventType.TOOL_CALL,
                    {"node": node_name, "action": "node_start"},
                    agent_id=node_name,
                )

            # Pre-execution: if state has messages and pins are active, reinject if needed
            working_state = dict(state)
            if self.enforce_pins and "messages" in working_state and isinstance(working_state["messages"], list):
                working_state["messages"] = reinject(working_state["messages"], self.pin_store)

            # Node execution
            result = fn(working_state)
            new_state = dict(working_state)
            if isinstance(result, dict):
                new_state.update(result)

            # Post-execution: ensure pins are intact in resulting messages
            if self.enforce_pins and "messages" in new_state and isinstance(new_state["messages"], list):
                new_state["messages"] = reinject(new_state["messages"], self.pin_store)

            if writer:
                writer.write(
                    EventType.TOOL_RESULT,
                    {"node": node_name, "action": "node_complete"},
                    agent_id=node_name,
                )

            return new_state

        return wrapped_node

    def check_installed(self) -> None:
        """Verify langgraph library is present."""
        _check_langgraph_installed()
