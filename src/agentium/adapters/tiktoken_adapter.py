"""TikToken Adapter for Agentium v2.

Provides exact token counting, encoding, and decoding for context compaction and budget tracking.
"""
from __future__ import annotations

from typing import List

from .._meta import PACKAGE_NAME

try:
    import tiktoken as _raw_tiktoken
except ImportError:
    _raw_tiktoken = None  # type: ignore


def _ensure_installed() -> None:
    if _raw_tiktoken is None:
        raise ImportError(
            f"TikToken adapter requires the 'tiktoken' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[tiktoken]'"
        )


raw = _raw_tiktoken


def _get_encoder(model_or_encoding: str):
    _ensure_installed()
    try:
        return _raw_tiktoken.encoding_for_model(model_or_encoding)
    except KeyError:
        return _raw_tiktoken.get_encoding(model_or_encoding)


def count_tokens(text: str, model_or_encoding: str = "cl100k_base") -> int:
    """Return exact token count for the given text."""
    enc = _get_encoder(model_or_encoding)
    return len(enc.encode(text, disallowed_special=()))


def encode(text: str, model_or_encoding: str = "cl100k_base") -> List[int]:
    """Encode text into token IDs."""
    enc = _get_encoder(model_or_encoding)
    return enc.encode(text, disallowed_special=())


def decode(tokens: List[int], model_or_encoding: str = "cl100k_base") -> str:
    """Decode token IDs back to a string."""
    enc = _get_encoder(model_or_encoding)
    return enc.decode(tokens)
