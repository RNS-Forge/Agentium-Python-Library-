"""PyBreaker Adapter for Agentium v2.

Provides circuit breaker protection wrapped with Agentium event emission and effect tags.
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run

try:
    import pybreaker as _raw_pybreaker
except ImportError:
    _raw_pybreaker = None  # type: ignore


def _ensure_installed():
    if _raw_pybreaker is None:
        raise ImportError(
            f"Pybreaker adapter requires the 'pybreaker' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[pybreaker]'"
        )


raw = _raw_pybreaker


def breaker(fail_max: int = 5, reset_timeout: int = 60, name: str = "default_breaker", effect: str = "read") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to wrap a function with a CircuitBreaker."""
    _ensure_installed()
    cb = _raw_pybreaker.CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout, name=name)

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = getattr(fn, "__name__", name)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "breaker": name, "state": str(cb.current_state)},
                )
            res = cb(fn)(*args, **kwargs)
            return res

        wrapper.raw = fn  # type: ignore
        wrapper.circuit_breaker = cb  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        return wrapper

    return decorator


def breaker_async(fail_max: int = 5, reset_timeout: int = 60, name: str = "default_async_breaker", effect: str = "read") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Async twin decorator to wrap a coroutine function with a CircuitBreaker."""
    _ensure_installed()
    cb = _raw_pybreaker.CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout, name=name)

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = getattr(fn, "__name__", name)

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "breaker": name, "state": str(cb.current_state), "async": True},
                )
            # Pybreaker supports async callables directly in 1.x
            res = await cb(fn)(*args, **kwargs)
            return res

        wrapper.raw = fn  # type: ignore
        wrapper.circuit_breaker = cb  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        return wrapper

    return decorator
