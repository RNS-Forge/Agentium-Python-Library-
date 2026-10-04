"""Recipe R03: cached_tool (cachetools + F1 claims + canonical hashing).

Caches a read-only tool by canonical argument hash, ensuring cached outputs
retain their claim and evidence links for provenance tracking.
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.hashing import sha256_hex
from ..core.run import get_current_run
from ..lineage.claims import EvidenceRef

T = TypeVar("T")


def cached_tool(
    fn: Optional[Callable[..., T]] = None,
    *,
    maxsize: int = 128,
    ttl: float = 300.0,
    name: Optional[str] = None,
    effect: str = "read",
) -> Any:
    """Decorator to cache a read-only tool using canonical argument hashing."""
    if effect.lower() != "read":
        raise ValueError(f"Recipe 'cached_tool' can only be applied to read tools (effect='read', got '{effect}').")

    def decorator(target_fn: Callable[..., T]) -> Callable[..., T]:
        tool_name = name or getattr(target_fn, "__name__", "cached_tool_fn")

        try:
            import cachetools
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'cached_tool' requires 'cachetools'. "
                f"Install via: pip install '{PACKAGE_NAME}[cachetools]'"
            ) from exc

        cache: Dict[str, Tuple[T, EvidenceRef]] = cachetools.TTLCache(maxsize=maxsize, ttl=ttl)

        @functools.wraps(target_fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate canonical hash of arguments
            arg_hash = sha256_hex({"args": args, "kwargs": kwargs})
            ctx = get_current_run()

            if arg_hash in cache:
                cached_res, evidence = cache[arg_hash]
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": tool_name, "cache_hit": True, "evidence_id": evidence.source_id},
                    )
                return cached_res

            # Fresh execution
            result = target_fn(*args, **kwargs)
            evidence = EvidenceRef(
                source_type="tool_call",
                source_id=f"{tool_name}_{arg_hash[:10]}",
                excerpt=str(result)[:200],
                hash=arg_hash,
            )
            cache[arg_hash] = (result, evidence)

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": tool_name, "cache_hit": False, "evidence_id": evidence.source_id},
                )
            return result

        wrapper.raw = target_fn  # type: ignore
        wrapper.cache = cache  # type: ignore
        wrapper.__agentium_tool_effect__ = "read"  # type: ignore
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def cached_tool_async(
    fn: Optional[Callable[..., Any]] = None,
    *,
    maxsize: int = 128,
    ttl: float = 300.0,
    name: Optional[str] = None,
    effect: str = "read",
) -> Any:
    """Async twin: Decorator to cache an async read-only tool."""
    if effect.lower() != "read":
        raise ValueError(f"Recipe 'cached_tool_async' can only be applied to read tools (effect='read', got '{effect}').")

    def decorator(target_fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or getattr(target_fn, "__name__", "cached_async_tool_fn")

        try:
            import cachetools
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'cached_tool_async' requires 'cachetools'. "
                f"Install via: pip install '{PACKAGE_NAME}[cachetools]'"
            ) from exc

        cache: Dict[str, Tuple[Any, EvidenceRef]] = cachetools.TTLCache(maxsize=maxsize, ttl=ttl)

        @functools.wraps(target_fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            arg_hash = sha256_hex({"args": args, "kwargs": kwargs})
            ctx = get_current_run()

            if arg_hash in cache:
                cached_res, evidence = cache[arg_hash]
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": tool_name, "cache_hit": True, "evidence_id": evidence.source_id, "async": True},
                    )
                return cached_res

            result = await target_fn(*args, **kwargs)
            evidence = EvidenceRef(
                source_type="tool_call",
                source_id=f"{tool_name}_{arg_hash[:10]}",
                excerpt=str(result)[:200],
                hash=arg_hash,
            )
            cache[arg_hash] = (result, evidence)

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": tool_name, "cache_hit": False, "evidence_id": evidence.source_id, "async": True},
                )
            return result

        wrapper.raw = target_fn  # type: ignore
        wrapper.cache = cache  # type: ignore
        wrapper.__agentium_tool_effect__ = "read"  # type: ignore
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator
