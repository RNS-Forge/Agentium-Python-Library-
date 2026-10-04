"""Recipe R28: api_call_safe (httpx + tenacity + pybreaker).

Safe HTTP read tool with retry, circuit breaker, and effect tagging ('effect=read'),
protecting agent pipelines from upstream network flapping and cascading failures.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run


def api_call_safe(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    max_attempts: int = 3,
    fail_max: int = 5,
    reset_timeout: int = 60,
    effect: str = "read",
    name: Optional[str] = None,
    client: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    """Execute a safe, resilient HTTP read call with retry and circuit breaker.

    Args:
        url: Target HTTP/HTTPS URL.
        method: HTTP method (must be read-only: GET, HEAD, OPTIONS).
        params: Query parameters.
        headers: Request headers.
        timeout: Request timeout in seconds.
        max_attempts: Max retry attempts on network error or 5xx.
        fail_max: Consecutive failures before circuit breaker trips.
        reset_timeout: Seconds before breaker resets.
        effect: Effect tag (strictly enforced to 'read').
        name: Tool/Call identifier for event tracing.
        client: Optional custom HTTP client or mock callable.
        **kwargs: Additional arguments forwarded to HTTP client.

    Returns:
        Response object or parsed dictionary.
    """
    if effect.lower() != "read":
        raise ValueError(f"Recipe 'api_call_safe' can only be applied to read operations (effect='read', got '{effect}').")

    if method.upper() not in {"GET", "HEAD", "OPTIONS"}:
        raise ValueError(f"Recipe 'api_call_safe' requires a read-only HTTP method ('GET', 'HEAD', 'OPTIONS'), got '{method}'.")

    try:
        import pybreaker
        import tenacity
    except ImportError as exc:
        raise ImportError(
            f"Recipe 'api_call_safe' requires 'tenacity' and 'pybreaker'. "
            f"Install via: pip install '{PACKAGE_NAME}[tenacity,pybreaker]'"
        ) from exc

    call_name = name or f"http_{method.lower()}_{url.split('?')[0]}"
    cb = pybreaker.CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout, name=call_name)
    retryer = tenacity.Retrying(
        stop=tenacity.stop_after_attempt(max_attempts),
        wait=tenacity.wait_exponential(multiplier=0.1, min=0.1, max=1.0),
        reraise=True,
    )

    ctx = get_current_run()
    if ctx and ctx.event_writer:
        ctx.event_writer.write(
            EventType.TOOL_CALL,
            {"tool_name": call_name, "effect": "read", "url": url, "method": method},
        )

    def _execute() -> Any:
        if client is not None:
            return client.request(method=method, url=url, params=params, headers=headers, timeout=timeout, **kwargs)
        try:
            from ..adapters import httpx_adapter
            resp = httpx_adapter.request(method=method, url=url, params=params, headers=headers, timeout=timeout, **kwargs)
            if hasattr(resp, "raise_for_status"):
                resp.raise_for_status()
            return resp
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'api_call_safe' requires 'httpx'. "
                f"Install via: pip install '{PACKAGE_NAME}[httpx]' or supply client."
            ) from exc

    try:
        for attempt in retryer:
            with attempt:
                result = cb(_execute)()
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": call_name, "effect": "read", "status": "success"},
                    )
                return result
    except Exception as exc:
        if ctx and ctx.event_writer:
            ctx.event_writer.write(
                EventType.TOOL_RESULT,
                {"tool_name": call_name, "effect": "read", "status": "error", "error": str(exc)},
            )
        raise


async def api_call_safe_async(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    max_attempts: int = 3,
    fail_max: int = 5,
    reset_timeout: int = 60,
    effect: str = "read",
    name: Optional[str] = None,
    client: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    """Async twin: Execute a safe, resilient HTTP read call with retry and circuit breaker."""
    return await asyncio.to_thread(
        api_call_safe,
        url=url,
        method=method,
        params=params,
        headers=headers,
        timeout=timeout,
        max_attempts=max_attempts,
        fail_max=fail_max,
        reset_timeout=reset_timeout,
        effect=effect,
        name=name,
        client=client,
        **kwargs,
    )
