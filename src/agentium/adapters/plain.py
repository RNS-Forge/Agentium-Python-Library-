from __future__ import annotations

import asyncio
import functools
import inspect
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TypeVar

from ..core.events import EventType
from ..core.run import get_current_run

F = TypeVar("F", bound=Callable[..., Any])

VALID_EFFECTS = {"read", "write", "destructive"}


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    effect: str
    fn: Callable[..., Any]
    doc: Optional[str] = None


class ToolRegistry:
    """In-memory registry of registered tools and their declared effect tags."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, effect: str, fn: Callable[..., Any], doc: Optional[str] = None) -> None:
        if effect not in VALID_EFFECTS:
            raise ValueError(f"Invalid effect '{effect}'. Must be one of {sorted(VALID_EFFECTS)}")
        self._tools[name] = ToolDefinition(name=name, effect=effect, fn=fn, doc=doc)

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_effect(self, name: str) -> Optional[str]:
        tool = self._tools.get(name)
        return tool.effect if tool else None

    def list_all(self) -> Dict[str, ToolDefinition]:
        return dict(self._tools)


_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    return _global_registry


def tool(
    name: Optional[str] = None,
    effect: str = "read",
    registry: Optional[ToolRegistry] = None,
) -> Callable[[F], F]:
    """Decorator for agent tools.
    - Registers tool effect ('read' | 'write' | 'destructive')
    - Logs tool_call and tool_result events if inside an active agentium.run
    - Preserves function signature, return values, and exceptions unchanged.
    """
    if effect not in VALID_EFFECTS:
        raise ValueError(f"Invalid effect '{effect}'. Must be one of {sorted(VALID_EFFECTS)}")

    reg = registry or _global_registry

    def decorator(fn: F) -> F:
        tool_name = name or fn.__name__
        reg.register(tool_name, effect, fn, doc=inspect.getdoc(fn))

        if asyncio.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                active_run = get_current_run()
                start_time = time.perf_counter()
                call_event = None
                if active_run:
                    call_event = active_run.log(
                        EventType.TOOL_CALL,
                        {
                            "tool": tool_name,
                            "effect": effect,
                            "args": kwargs if kwargs else {"_args": list(args)},
                        },
                    )

                parent_id = call_event.event_id if call_event else None
                try:
                    res = await fn(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    if active_run:
                        active_run.log(
                            EventType.TOOL_RESULT,
                            {
                                "tool": tool_name,
                                "effect": effect,
                                "duration_ms": duration_ms,
                                "success": True,
                                "result": res,
                            },
                            parent_id=parent_id,
                        )
                    return res
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    if active_run:
                        active_run.log(
                            EventType.TOOL_RESULT,
                            {
                                "tool": tool_name,
                                "effect": effect,
                                "duration_ms": duration_ms,
                                "success": False,
                                "error": str(e),
                            },
                            parent_id=parent_id,
                        )
                    raise

            return async_wrapper  # type: ignore
        else:

            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                active_run = get_current_run()
                start_time = time.perf_counter()
                call_event = None
                if active_run:
                    call_event = active_run.log(
                        EventType.TOOL_CALL,
                        {
                            "tool": tool_name,
                            "effect": effect,
                            "args": kwargs if kwargs else {"_args": list(args)},
                        },
                    )

                parent_id = call_event.event_id if call_event else None
                try:
                    res = fn(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    if active_run:
                        active_run.log(
                            EventType.TOOL_RESULT,
                            {
                                "tool": tool_name,
                                "effect": effect,
                                "duration_ms": duration_ms,
                                "success": True,
                                "result": res,
                            },
                            parent_id=parent_id,
                        )
                    return res
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    if active_run:
                        active_run.log(
                            EventType.TOOL_RESULT,
                            {
                                "tool": tool_name,
                                "effect": effect,
                                "duration_ms": duration_ms,
                                "success": False,
                                "error": str(e),
                            },
                            parent_id=parent_id,
                        )
                    raise

            return sync_wrapper  # type: ignore

    return decorator
