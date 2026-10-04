"""Recipe R51: http_cache_tool (cachetools + httpx).

A cached read-only HTTP tool keyed by canonical request arguments,
preventing redundant upstream network calls while ensuring claim-linked provenance.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.hashing import sha256_hex
from ..core.run import get_current_run


class HttpCacheTool:
    """Read-only HTTP client cache keyed by canonical request signatures."""

    def __init__(self, maxsize: int = 128, ttl: float = 300.0, client: Optional[Any] = None) -> None:
        try:
            import cachetools
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'http_cache_tool' requires 'cachetools'. "
                f"Install via: pip install '{PACKAGE_NAME}[cachetools]'"
            ) from exc

        self.cache: Dict[str, Any] = cachetools.TTLCache(maxsize=maxsize, ttl=ttl)
        self.client = client

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        effect: str = "read",
        **kwargs: Any,
    ) -> Any:
        """Execute cached HTTP GET request enforcing read-only semantics."""
        if effect.lower() != "read":
            raise ValueError(f"Recipe 'http_cache_tool' strictly requires effect='read', got '{effect}'.")

        req_signature = sha256_hex({"url": url, "params": params or {}, "headers": headers or {}})
        ctx = get_current_run()

        # Check Cache
        if req_signature in self.cache:
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"recipe": "http_cache_tool", "url": url, "cache_hit": True, "effect": "read"},
                )
            return self.cache[req_signature]

        # Fresh request
        if ctx and ctx.event_writer:
            ctx.event_writer.write(
                EventType.TOOL_CALL,
                {"recipe": "http_cache_tool", "url": url, "cache_hit": False, "effect": "read"},
            )

        if self.client is not None:
            resp = self.client.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
        else:
            try:
                from ..adapters import httpx_adapter
                resp = httpx_adapter.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
                if hasattr(resp, "json"):
                    try:
                        resp = resp.json()
                    except Exception:
                        resp = resp.text
            except ImportError as exc:
                raise ImportError(
                    f"Recipe 'http_cache_tool' requires 'httpx'. "
                    f"Install via: pip install '{PACKAGE_NAME}[httpx]' or supply client."
                ) from exc

        self.cache[req_signature] = resp
        if ctx and ctx.event_writer:
            ctx.event_writer.write(
                EventType.TOOL_RESULT,
                {"recipe": "http_cache_tool", "url": url, "status": "success", "effect": "read"},
            )
        return resp

    async def get_async(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        effect: str = "read",
        **kwargs: Any,
    ) -> Any:
        """Async twin: Execute cached HTTP GET request enforcing read-only semantics."""
        return await asyncio.to_thread(
            self.get,
            url=url,
            params=params,
            headers=headers,
            timeout=timeout,
            effect=effect,
            **kwargs,
        )


def http_cache_tool(maxsize: int = 128, ttl: float = 300.0, client: Optional[Any] = None) -> HttpCacheTool:
    """Create an HttpCacheTool instance for cached read-only HTTP calls."""
    return HttpCacheTool(maxsize=maxsize, ttl=ttl, client=client)


async def http_cache_tool_async(maxsize: int = 128, ttl: float = 300.0, client: Optional[Any] = None) -> HttpCacheTool:
    """Async twin: Create an HttpCacheTool instance for cached read-only HTTP calls."""
    return await asyncio.to_thread(http_cache_tool, maxsize=maxsize, ttl=ttl, client=client)
