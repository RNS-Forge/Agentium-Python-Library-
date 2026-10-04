"""RapidFuzz Adapter for Agentium v2.

Provides fast, deterministic string similarity scoring for claim grounding and deduplication.
"""
from __future__ import annotations

from typing import Any

from .._meta import PACKAGE_NAME

try:
    from rapidfuzz import fuzz as _raw_fuzz
except ImportError:
    _raw_fuzz = None  # type: ignore


def _ensure_installed():
    if _raw_fuzz is None:
        raise ImportError(
            f"RapidFuzz adapter requires the 'rapidfuzz' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[rapidfuzz]'"
        )


raw = _raw_fuzz


def ratio(s1: str, s2: str) -> float:
    """Calculate normalized similarity ratio in range [0.0, 1.0]."""
    _ensure_installed()
    return float(_raw_fuzz.ratio(s1, s2)) / 100.0


def partial_ratio(s1: str, s2: str) -> float:
    """Calculate partial substring similarity ratio in range [0.0, 1.0]."""
    _ensure_installed()
    return float(_raw_fuzz.partial_ratio(s1, s2)) / 100.0
