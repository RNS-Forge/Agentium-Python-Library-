"""Tenacity Adapter for Agentium v2.

Provides resilient retry capabilities wrapped with Agentium event emission and effect tags.
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from .._meta import PACKAGE_NAME
from ..core.events import EventType, EventWriter
from ..core.run import get_current_run

try:
    import tenacity as _raw_tenacity
except ImportError:
    _raw_tenacity = None  # type: ignore


def _ensure_installed():
    if _raw_tenacity is None:
        raise ImportError(
            f"Tenacity adapter requires the 'tenacity' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[tenacity]'"
        )


raw = _raw_tenacity


def retry(*dargs: Any, name: Optional[str] = None, effect: str = "read", **dkwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to retry a function using tenacity with Agentium event emission."""
    _ensure_installed()

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tenacity_wrapped = _raw_tenacity.retry(*dargs, **dkwargs)(fn)
        tool_name = name or getattr(fn, "__name__", "retried_callable")

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "effect": effect, "action": "retry_start"},
                )

            res = tenacity_wrapped(*args, **kwargs)

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": tool_name, "effect": effect, "action": "retry_success"},
                )
            return res

        wrapper.raw = fn  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        return wrapper

    return decorator


def retry_async(*dargs: Any, name: Optional[str] = None, effect: str = "read", **dkwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Async twin decorator to retry a coroutine function using tenacity."""
    _ensure_installed()

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tenacity_wrapped = _raw_tenacity.retry(*dargs, **dkwargs)(fn)
        tool_name = name or getattr(fn, "__name__", "retried_async_callable")

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "effect": effect, "action": "retry_start", "async": True},
                )

            res = await tenacity_wrapped(*args, **kwargs)

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": tool_name, "effect": effect, "action": "retry_success", "async": True},
                )
            return res

        wrapper.raw = fn  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        return wrapper

    return decorator
