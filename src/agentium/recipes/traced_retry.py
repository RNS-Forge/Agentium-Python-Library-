"""Recipe R39: traced_retry (tenacity + OpenTelemetry + Agentium events).

A resilient retry decorator where every individual attempt emits an Agentium event
and (optionally) an OpenTelemetry trace span with full error context.
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


def traced_retry(
    fn: Optional[Callable[..., T]] = None,
    *,
    max_attempts: int = 3,
    wait_min: float = 0.1,
    wait_max: float = 2.0,
    name: Optional[str] = None,
    use_otel: bool = False,
) -> Any:
    """Decorator retrying transient failures while recording each attempt in events and trace spans."""
    def decorator(target_fn: Callable[..., T]) -> Callable[..., T]:
        tool_name = name or getattr(target_fn, "__name__", "traced_fn")

        try:
            import tenacity
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'traced_retry' requires 'tenacity'. "
                f"Install via: pip install '{PACKAGE_NAME}[tenacity]'"
            ) from exc

        tracer = None
        if use_otel:
            try:
                from ..core.otel import get_tracer
                tracer = get_tracer("agentium.retry")
            except ImportError:
                tracer = None

        retryer = tenacity.Retrying(
            stop=tenacity.stop_after_attempt(max_attempts),
            wait=tenacity.wait_exponential(multiplier=0.1, min=wait_min, max=wait_max),
            reraise=True,
        )

        @functools.wraps(target_fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt_idx = 0

            for attempt in retryer:
                with attempt:
                    attempt_idx += 1
                    ctx = get_current_run()
                    t0 = time.perf_counter()

                    if ctx and ctx.event_writer:
                        ctx.event_writer.write(
                            EventType.TOOL_CALL,
                            {
                                "recipe": "traced_retry",
                                "target": tool_name,
                                "attempt_number": attempt_idx,
                                "max_attempts": max_attempts,
                            },
                        )

                    span_ctx = None
                    if tracer is not None:
                        span_ctx = tracer.start_as_current_span(f"retry.{tool_name}.attempt_{attempt_idx}")

                    try:
                        if span_ctx:
                            with span_ctx:
                                res = target_fn(*args, **kwargs)
                        else:
                            res = target_fn(*args, **kwargs)

                        if ctx and ctx.event_writer:
                            duration_ms = (time.perf_counter() - t0) * 1000.0
                            ctx.event_writer.write(
                                EventType.TOOL_RESULT,
                                {
                                    "recipe": "traced_retry",
                                    "target": tool_name,
                                    "attempt_number": attempt_idx,
                                    "status": "success",
                                    "duration_ms": duration_ms,
                                },
                            )
                        return res
                    except Exception as err:
                        if ctx and ctx.event_writer:
                            duration_ms = (time.perf_counter() - t0) * 1000.0
                            ctx.event_writer.write(
                                EventType.TOOL_RESULT,
                                {
                                    "recipe": "traced_retry",
                                    "target": tool_name,
                                    "attempt_number": attempt_idx,
                                    "status": "attempt_failed",
                                    "error": str(err),
                                    "duration_ms": duration_ms,
                                },
                            )
                        raise

            raise RuntimeError("traced_retry exhausted all retry attempts.")

        wrapper.raw = target_fn  # type: ignore
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def traced_retry_async(
    fn: Optional[Callable[..., Any]] = None,
    *,
    max_attempts: int = 3,
    wait_min: float = 0.1,
    wait_max: float = 2.0,
    name: Optional[str] = None,
    use_otel: bool = False,
) -> Any:
    """Async twin: Decorator retrying transient failures while recording each attempt."""
    def decorator(target_fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or getattr(target_fn, "__name__", "traced_async_fn")

        try:
            import tenacity
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'traced_retry' requires 'tenacity'. "
                f"Install via: pip install '{PACKAGE_NAME}[tenacity]'"
            ) from exc

        @functools.wraps(target_fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt_idx = 0
            while attempt_idx < max_attempts:
                attempt_idx += 1
                ctx = get_current_run()
                t0 = time.perf_counter()

                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_CALL,
                        {
                            "recipe": "traced_retry",
                            "target": tool_name,
                            "attempt_number": attempt_idx,
                            "async": True,
                        },
                    )

                try:
                    if asyncio.iscoroutinefunction(target_fn):
                        res = await target_fn(*args, **kwargs)
                    else:
                        res = await asyncio.to_thread(target_fn, *args, **kwargs)

                    if ctx and ctx.event_writer:
                        ctx.event_writer.write(
                            EventType.TOOL_RESULT,
                            {
                                "recipe": "traced_retry",
                                "target": tool_name,
                                "attempt_number": attempt_idx,
                                "status": "success",
                                "async": True,
                            },
                        )
                    return res
                except Exception as exc:
                    if ctx and ctx.event_writer:
                        ctx.event_writer.write(
                            EventType.TOOL_RESULT,
                            {
                                "recipe": "traced_retry",
                                "target": tool_name,
                                "attempt_number": attempt_idx,
                                "status": "attempt_failed",
                                "error": str(exc),
                                "async": True,
                            },
                        )
                    if attempt_idx >= max_attempts:
                        raise
                    await asyncio.sleep(min(wait_min * (2 ** (attempt_idx - 1)), wait_max))

            raise RuntimeError("traced_retry_async exhausted all retry attempts.")

        async_wrapper.raw = target_fn  # type: ignore
        return async_wrapper

    if fn is not None:
        return decorator(fn)
    return decorator
