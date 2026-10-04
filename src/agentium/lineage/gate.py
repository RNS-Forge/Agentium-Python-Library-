"""F4: Action Gate (Shadow & Enforce mode tool safety)."""
from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ..core.events import EventType, EventWriter
from ..core.run import get_current_run
from .claims import Claim


class ActionBlockedError(PermissionError):
    """Raised when ActionGate blocks tool execution."""


class ActionGate:
    """Policy enforcement engine controlling tool execution based on side-effects and claims."""

    def __init__(
        self,
        mode: str = "enforce",  # "enforce" or "shadow"
        on_destructive_undeclared: str = "escalate",  # "allow", "block", "escalate"
        event_writer: Optional[EventWriter] = None,
    ) -> None:
        self.mode = mode.lower()
        self.on_destructive_undeclared = on_destructive_undeclared.lower()
        self.event_writer = event_writer

    def _emit(self, event_type: Union[EventType, str], payload: Dict[str, Any]) -> None:
        writer = self.event_writer
        if writer is None:
            ctx = get_current_run()
            if ctx is not None:
                writer = ctx.event_writer
        if writer is not None:
            writer.write(event_type, payload)

    def evaluate(
        self,
        tool_name: str,
        effect: str = "read",
        arguments: Optional[Dict[str, Any]] = None,
        claims: Optional[List[Claim]] = None,
        human_confirmed: bool = False,
    ) -> Tuple[bool, str]:
        """Evaluate if an action is permitted.

        Returns:
            (allowed: bool, reason: str)
        """
        effect = effect.lower()

        # 1. Read operations are always safe
        if effect == "read":
            return True, "Read operations are unconditionally permitted."

        # 2. Write operations: permitted unless explicitly restricted
        if effect == "write":
            return True, "Write operation authorized."

        # 3. Destructive operations (drop, delete, format, alter)
        if effect == "destructive":
            # Human confirmation always authorizes
            if human_confirmed:
                return True, "Destructive operation authorized by human-in-the-loop confirmation."

            # Check if grounded by verified high-confidence claim
            if claims:
                for c in claims:
                    if c.status == "verified" and c.confidence >= 0.9:
                        return True, f"Destructive operation grounded by verified claim '{c.id}'."

            # Neither human confirmation nor verified claim present
            reason = (
                f"Destructive tool '{tool_name}' blocked: requires human confirmation "
                "or a verified claim with confidence >= 0.9."
            )
            return False, reason

        # Unknown effect
        return False, f"Unknown tool effect '{effect}'."

    def execute_guarded(
        self,
        func: Callable[..., Any],
        effect: str,
        *args: Any,
        claims: Optional[List[Claim]] = None,
        human_confirmed: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Evaluate gate and execute callable if authorized."""
        tool_name = getattr(func, "__name__", "anonymous_tool")
        allowed, reason = self.evaluate(
            tool_name=tool_name,
            effect=effect,
            arguments=kwargs,
            claims=claims,
            human_confirmed=human_confirmed,
        )

        payload = {
            "tool_name": tool_name,
            "effect": effect,
            "allowed": allowed,
            "reason": reason,
            "mode": self.mode,
        }

        if not allowed:
            if self.mode == "enforce":
                self._emit(EventType.ACTION_GATE_BLOCK, payload)
                raise ActionBlockedError(reason)
            else:
                # Shadow mode: record shadow block event but allow execution
                self._emit(EventType.ACTION_GATE_SHADOW_BLOCK, payload)
                return func(*args, **kwargs)

        return func(*args, **kwargs)


def guarded(
    gate: Optional[ActionGate] = None,
    effect: str = "read",
):
    """Decorator to enforce or shadow action safety on tools."""
    def decorator(fn: Callable[..., Any]):
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            actual_gate = gate or ActionGate()
            # Extract optional claims or human_confirmed passed in kwargs
            claims = kwargs.pop("__claims__", None)
            human_confirmed = kwargs.pop("__human_confirmed__", False)
            return actual_gate.execute_guarded(
                fn, effect, *args, claims=claims, human_confirmed=human_confirmed, **kwargs
            )
        # Preserve original attributes
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        return wrapper
    return decorator
