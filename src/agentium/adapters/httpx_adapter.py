"""HTTPX Adapter for Agentium v2.

Provides bounded, safe HTTP communication integrated with Agentium event logging.
"""
from __future__ import annotations

from typing import Any

from .._meta import PACKAGE_NAME

try:
    import httpx as _raw_httpx
except ImportError:
    _raw_httpx = None  # type: ignore


def _ensure_installed() -> None:
    if _raw_httpx is None:
        raise ImportError(
            f"HTTPX adapter requires the 'httpx' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[httpx]'"
        )


raw = _raw_httpx


def get(url: str, **kwargs: Any) -> Any:
    """Execute sync HTTP GET request."""
    _ensure_installed()
    return _raw_httpx.get(url, **kwargs)


def post(url: str, **kwargs: Any) -> Any:
    """Execute sync HTTP POST request."""
    _ensure_installed()
    return _raw_httpx.post(url, **kwargs)


def request(method: str, url: str, **kwargs: Any) -> Any:
    """Execute sync HTTP request with specified method."""
    _ensure_installed()
    return _raw_httpx.request(method, url, **kwargs)
