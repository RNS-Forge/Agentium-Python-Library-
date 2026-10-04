"""OpenAI Agents SDK Adapter for Agentium v2.

Integrates ActionGate safety checks, tool interceptors, and run events.
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Dict, List, Optional

from ..core.events import EventType, EventWriter
from ..core.run import get_current_run
from ..lineage.claims import Claim
from ..lineage.gate import ActionBlockedError, ActionGate


def _check_openai_installed() -> None:
    try:
        import openai  # type: ignore # noqa: F401
    except ImportError as e:
        raise ImportError(
            "OpenAI Agents adapter requires 'openai'. "
            "Install it via: pip install 'agentium[openai-agents]'"
        ) from e


class OpenAIAgentsAdapter:
    """Adapter bridging OpenAI agent execution to Agentium ActionGate and events."""

    def __init__(
        self,
        gate: Optional[ActionGate] = None,
        event_writer: Optional[EventWriter] = None,
    ) -> None:
        self.gate = gate or ActionGate()
        self.event_writer = event_writer

    def _get_writer(self) -> Optional[EventWriter]:
        if self.event_writer is not None:
            return self.event_writer
        ctx = get_current_run()
        return ctx.event_writer if ctx is not None else None

    def guard_tool(
        self,
        tool_fn: Callable[..., Any],
        effect: str = "read",
        claims: Optional[List[Claim]] = None,
    ) -> Callable[..., Any]:
        """Wrap an OpenAI agent tool function with Agentium ActionGate checks."""
        @functools.wraps(tool_fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            human_confirmed = kwargs.pop("__human_confirmed__", False)
            writer = self._get_writer()
            tool_name = getattr(tool_fn, "__name__", "openai_tool")

            if writer:
                writer.write(
                    EventType.TOOL_CALL,
                    {"tool": tool_name, "effect": effect, "arguments": kwargs},
                )

            # Evaluate through gate
            res = self.gate.execute_guarded(
                tool_fn,
                effect,
                *args,
                claims=claims,
                human_confirmed=human_confirmed,
                **kwargs,
            )

            if writer:
                writer.write(
                    EventType.TOOL_RESULT,
                    {"tool": tool_name, "effect": effect},
                )

            return res

        return wrapper

    def check_installed(self) -> None:
        """Verify openai library is present."""
        _check_openai_installed()
