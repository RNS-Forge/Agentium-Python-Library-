"""Recipe R01: safe_call (tenacity + pybreaker + stdlib timeout).

Retries transient failures with backoff, trips a circuit breaker after
repeated failures, enforces deadlines, and logs every step through Agentium.
"""
from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable, Optional, TypeVar

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run

T = TypeVar("T")


def safe_call(
    fn: Optional[Callable[..., T]] = None,
    *,
    max_attempts: int = 3,
    fail_max: int = 5,
    reset_timeout: int = 60,
    timeout_seconds: Optional[float] = None,
    name: Optional[str] = None,
    effect: str = "read",
) -> Any:
    """Execute or decorate a callable with retry, circuit breaker, and timeout."""
    def decorator(target_fn: Callable[..., T]) -> Callable[..., T]:
        tool_name = name or getattr(target_fn, "__name__", "safe_call_fn")

        try:
            import pybreaker
            import tenacity
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'safe_call' requires 'tenacity' and 'pybreaker'. "
                f"Install via: pip install '{PACKAGE_NAME}[tenacity,pybreaker]'"
            ) from exc

        cb = pybreaker.CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout, name=tool_name)

        retryer = tenacity.Retrying(
            stop=tenacity.stop_after_attempt(max_attempts),
            wait=tenacity.wait_exponential(multiplier=0.1, min=0.1, max=2.0),
            reraise=True,
        )

        @functools.wraps(target_fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "recipe": "safe_call", "effect": effect},
                )

            t0 = time.time()

            def execute_attempt():
                if timeout_seconds is not None and (time.time() - t0) > timeout_seconds:
                    raise TimeoutError(f"Operation '{tool_name}' exceeded timeout of {timeout_seconds}s")
                return cb(target_fn)(*args, **kwargs)

            try:
                res = retryer(execute_attempt)
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": tool_name, "recipe": "safe_call", "status": "success"},
                    )
                return res
            except Exception as e:
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": tool_name, "recipe": "safe_call", "status": "error", "error": type(e).__name__},
                    )
                raise

        wrapper.raw = target_fn  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def safe_call_async(
    fn: Optional[Callable[..., Any]] = None,
    *,
    max_attempts: int = 3,
    fail_max: int = 5,
    reset_timeout: int = 60,
    timeout_seconds: Optional[float] = None,
    name: Optional[str] = None,
    effect: str = "read",
) -> Any:
    """Async twin: execute or decorate a coroutine function with retry, circuit breaker, and timeout."""
    def decorator(target_fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or getattr(target_fn, "__name__", "safe_call_async_fn")

        try:
            import pybreaker
            import tenacity
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'safe_call_async' requires 'tenacity' and 'pybreaker'. "
                f"Install via: pip install '{PACKAGE_NAME}[tenacity,pybreaker]'"
            ) from exc

        cb = pybreaker.CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout, name=tool_name)

        async_retryer = tenacity.AsyncRetrying(
            stop=tenacity.stop_after_attempt(max_attempts),
            wait=tenacity.wait_exponential(multiplier=0.1, min=0.1, max=2.0),
            reraise=True,
        )

        @functools.wraps(target_fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "recipe": "safe_call", "effect": effect, "async": True},
                )

            async def execute_attempt():
                coro = cb(target_fn)(*args, **kwargs)
                if timeout_seconds is not None:
                    return await asyncio.wait_for(coro, timeout=timeout_seconds)
                return await coro

            try:
                res = await async_retryer(execute_attempt)
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": tool_name, "recipe": "safe_call", "status": "success", "async": True},
                    )
                return res
            except Exception as e:
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": tool_name, "recipe": "safe_call", "status": "error", "error": type(e).__name__, "async": True},
                    )
                raise

        wrapper.raw = target_fn  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator
