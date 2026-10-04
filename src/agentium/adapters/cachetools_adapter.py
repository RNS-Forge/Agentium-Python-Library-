"""Cachetools Adapter for Agentium v2.

Provides in-memory TTL caching with canonical hashing and Agentium effect tags.
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Dict, Optional

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.hashing import sha256_hex
from ..core.run import get_current_run

try:
    import cachetools as _raw_cachetools
except ImportError:
    _raw_cachetools = None  # type: ignore


def _ensure_installed():
    if _raw_cachetools is None:
        raise ImportError(
            f"Cachetools adapter requires the 'cachetools' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[cachetools]'"
        )


raw = _raw_cachetools


def ttl_cache(maxsize: int = 128, ttl: float = 300.0, name: Optional[str] = None, effect: str = "read") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to cache a function's results in a TTLCache using canonical JSON hashing."""
    _ensure_installed()
    cache = _raw_cachetools.TTLCache(maxsize=maxsize, ttl=ttl)

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or getattr(fn, "__name__", "cached_fn")

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = sha256_hex({"args": args, "kwargs": kwargs})
            ctx = get_current_run()

            if key in cache:
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": tool_name, "cache_hit": True, "key": key[:12]},
                    )
                return cache[key]

            result = fn(*args, **kwargs)
            cache[key] = result

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": tool_name, "cache_hit": False, "key": key[:12]},
                )
            return result

        wrapper.raw = fn  # type: ignore
        wrapper.cache = cache  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        return wrapper

    return decorator


def ttl_cache_async(maxsize: int = 128, ttl: float = 300.0, name: Optional[str] = None, effect: str = "read") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Async twin decorator to cache coroutine results in a TTLCache."""
    _ensure_installed()
    cache = _raw_cachetools.TTLCache(maxsize=maxsize, ttl=ttl)

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or getattr(fn, "__name__", "cached_async_fn")

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = sha256_hex({"args": args, "kwargs": kwargs})
            ctx = get_current_run()

            if key in cache:
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": tool_name, "cache_hit": True, "key": key[:12], "async": True},
                    )
                return cache[key]

            result = await fn(*args, **kwargs)
            cache[key] = result

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": tool_name, "cache_hit": False, "key": key[:12], "async": True},
                )
            return result

        wrapper.raw = fn  # type: ignore
        wrapper.cache = cache  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        return wrapper

    return decorator
