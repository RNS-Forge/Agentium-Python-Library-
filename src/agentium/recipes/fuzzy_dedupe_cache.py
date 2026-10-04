"""Recipe R58: fuzzy_dedupe_cache (rapidfuzz + cachetools).

Reuses a cached tool result if incoming text arguments are near-identical (similarity >= threshold)
AND the tool is strictly verified to be read-only ('effect=read').
"""
from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run

T = TypeVar("T")


def fuzzy_dedupe_cache(
    fn: Optional[Callable[..., T]] = None,
    *,
    threshold: float = 0.90,
    maxsize: int = 128,
    ttl: float = 300.0,
    effect: str = "read",
    name: Optional[str] = None,
) -> Any:
    """Decorator to deduplicate and cache read-only tool calls by fuzzy string similarity."""
    if effect.lower() != "read":
        raise ValueError(f"Recipe 'fuzzy_dedupe_cache' can only be applied to read tools (effect='read', got '{effect}').")

    norm_threshold = threshold / 100.0 if threshold > 1.0 else threshold

    def decorator(target_fn: Callable[..., T]) -> Callable[..., T]:
        tool_name = name or getattr(target_fn, "__name__", "fuzzy_cached_tool")

        try:
            import cachetools
            from ..adapters import rapidfuzz_adapter
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'fuzzy_dedupe_cache' requires 'cachetools' and 'rapidfuzz'. "
                f"Install via: pip install '{PACKAGE_NAME}[cachetools,rapidfuzz]'"
            ) from exc

        # Cache entries store: query_key -> (timestamp, output)
        entries: List[Tuple[str, float, T]] = []

        @functools.wraps(target_fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Build unified text query representation from args
            query_str = " ".join([str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())])
            now = time.time()
            ctx = get_current_run()

            # Evict expired entries
            nonlocal entries
            entries = [(q, ts, out) for q, ts, out in entries if (now - ts) < ttl]

            # Search for best match above threshold
            best_match: Optional[Tuple[str, float, T]] = None
            highest_score: float = 0.0

            for q, ts, out in entries:
                score = rapidfuzz_adapter.ratio(query_str, q)
                if score >= norm_threshold and score > highest_score:
                    highest_score = score
                    best_match = (q, ts, out)

            if best_match is not None:
                matched_query, _, cached_res = best_match
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {
                            "recipe": "fuzzy_dedupe_cache",
                            "tool_name": tool_name,
                            "fuzzy_cache_hit": True,
                            "similarity_score": highest_score,
                            "matched_query": matched_query[:100],
                            "effect": "read",
                        },
                    )
                return cached_res

            # Cache miss - execute fresh
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"recipe": "fuzzy_dedupe_cache", "tool_name": tool_name, "effect": "read"},
                )

            res = target_fn(*args, **kwargs)

            # Insert into cache (evict oldest if exceeds maxsize)
            if len(entries) >= maxsize:
                entries.pop(0)
            entries.append((query_str, now, res))

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"recipe": "fuzzy_dedupe_cache", "tool_name": tool_name, "status": "success", "effect": "read"},
                )
            return res

        wrapper.raw = target_fn  # type: ignore
        wrapper.__agentium_tool_effect__ = "read"  # type: ignore
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def fuzzy_dedupe_cache_async(
    fn: Optional[Callable[..., Any]] = None,
    *,
    threshold: float = 0.90,
    maxsize: int = 128,
    ttl: float = 300.0,
    effect: str = "read",
    name: Optional[str] = None,
) -> Any:
    """Async twin: Decorator to deduplicate and cache read-only tool calls by fuzzy string similarity."""
    sync_dec = fuzzy_dedupe_cache(threshold=threshold, maxsize=maxsize, ttl=ttl, effect=effect, name=name)

    def decorator(target_fn: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(target_fn):
            # For coroutine functions, run through async executor
            tool_name = name or getattr(target_fn, "__name__", "async_fuzzy_cached_tool")
            norm_threshold = threshold / 100.0 if threshold > 1.0 else threshold
            entries: List[Tuple[str, float, Any]] = []

            @functools.wraps(target_fn)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                from ..adapters import rapidfuzz_adapter
                query_str = " ".join([str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())])
                now = time.time()
                ctx = get_current_run()

                nonlocal entries
                entries = [(q, ts, out) for q, ts, out in entries if (now - ts) < ttl]

                best_match = None
                highest_score = 0.0
                for q, ts, out in entries:
                    score = rapidfuzz_adapter.ratio(query_str, q)
                    if score >= norm_threshold and score > highest_score:
                        highest_score = score
                        best_match = (q, ts, out)

                if best_match is not None:
                    if ctx and ctx.event_writer:
                        ctx.event_writer.write(
                            EventType.TOOL_RESULT,
                            {"recipe": "fuzzy_dedupe_cache", "tool_name": tool_name, "fuzzy_cache_hit": True, "score": highest_score},
                        )
                    return best_match[2]

                res = await target_fn(*args, **kwargs)
                if len(entries) >= maxsize:
                    entries.pop(0)
                entries.append((query_str, now, res))
                return res

            wrapper.raw = target_fn  # type: ignore
            wrapper.__agentium_tool_effect__ = "read"  # type: ignore
            return wrapper

        return sync_dec(target_fn)

    if fn is not None:
        return decorator(fn)
    return decorator
