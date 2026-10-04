"""Recipe R42: graph_retry (langgraph + tenacity).

Wraps LangGraph workflow node functions with an automated retry policy and backoff,
recording node retry attempts and exceptions in Agentium event logs.
"""
from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, Dict, Optional, TypeVar

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run

T = TypeVar("T")


def graph_retry(
    node_fn: Optional[Callable[..., T]] = None,
    *,
    max_attempts: int = 3,
    wait_min: float = 0.1,
    wait_max: float = 2.0,
    name: Optional[str] = None,
) -> Any:
    """Decorator retrying LangGraph node invocations with exponential backoff and event tracing."""
    def decorator(target_fn: Callable[..., T]) -> Callable[..., T]:
        node_name = name or getattr(target_fn, "__name__", "graph_node")

        try:
            import tenacity
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'graph_retry' requires 'tenacity'. "
                f"Install via: pip install '{PACKAGE_NAME}[tenacity]'"
            ) from exc

        retryer = tenacity.Retrying(
            stop=tenacity.stop_after_attempt(max_attempts),
            wait=tenacity.wait_exponential(multiplier=0.1, min=wait_min, max=wait_max),
            reraise=True,
        )

        @functools.wraps(target_fn)
        def wrapper(state: Dict[str, Any], *args: Any, **kwargs: Any) -> T:
            attempt_idx = 0
            for attempt in retryer:
                with attempt:
                    attempt_idx += 1
                    ctx = get_current_run()
                    if ctx and ctx.event_writer:
                        ctx.event_writer.write(
                            EventType.TOOL_CALL,
                            {
                                "recipe": "graph_retry",
                                "node": node_name,
                                "attempt": attempt_idx,
                                "state_keys": list(state.keys()) if isinstance(state, dict) else [],
                            },
                        )

                    try:
                        res = target_fn(state, *args, **kwargs)
                        if ctx and ctx.event_writer:
                            ctx.event_writer.write(
                                EventType.TOOL_RESULT,
                                {"recipe": "graph_retry", "node": node_name, "status": "success", "attempt": attempt_idx},
                            )
                        return res
                    except Exception as err:
                        if ctx and ctx.event_writer:
                            ctx.event_writer.write(
                                EventType.TOOL_RESULT,
                                {"recipe": "graph_retry", "node": node_name, "status": "error", "error": str(err), "attempt": attempt_idx},
                            )
                        raise

            raise RuntimeError(f"LangGraph node '{node_name}' failed after {max_attempts} attempts.")

        wrapper.raw = target_fn  # type: ignore
        return wrapper

    if node_fn is not None:
        return decorator(node_fn)
    return decorator


def graph_retry_async(
    node_fn: Optional[Callable[..., Any]] = None,
    *,
    max_attempts: int = 3,
    wait_min: float = 0.1,
    wait_max: float = 2.0,
    name: Optional[str] = None,
) -> Any:
    """Async twin: Decorator retrying LangGraph node invocations with exponential backoff."""
    def decorator(target_fn: Callable[..., Any]) -> Callable[..., Any]:
        node_name = name or getattr(target_fn, "__name__", "async_graph_node")

        @functools.wraps(target_fn)
        async def wrapper(state: Dict[str, Any], *args: Any, **kwargs: Any) -> Any:
            attempt_idx = 0
            while attempt_idx < max_attempts:
                attempt_idx += 1
                ctx = get_current_run()
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_CALL,
                        {
                            "recipe": "graph_retry",
                            "node": node_name,
                            "attempt": attempt_idx,
                            "async": True,
                        },
                    )

                try:
                    if asyncio.iscoroutinefunction(target_fn):
                        res = await target_fn(state, *args, **kwargs)
                    else:
                        res = await asyncio.to_thread(target_fn, state, *args, **kwargs)

                    if ctx and ctx.event_writer:
                        ctx.event_writer.write(
                            EventType.TOOL_RESULT,
                            {"recipe": "graph_retry", "node": node_name, "status": "success", "async": True},
                        )
                    return res
                except Exception as exc:
                    if ctx and ctx.event_writer:
                        ctx.event_writer.write(
                            EventType.TOOL_RESULT,
                            {"recipe": "graph_retry", "node": node_name, "status": "error", "error": str(exc), "async": True},
                        )
                    if attempt_idx >= max_attempts:
                        raise
                    await asyncio.sleep(min(wait_min * (2 ** (attempt_idx - 1)), wait_max))

            raise RuntimeError(f"LangGraph async node '{node_name}' failed after {max_attempts} attempts.")

        wrapper.raw = target_fn  # type: ignore
        return wrapper

    if node_fn is not None:
        return decorator(node_fn)
    return decorator
