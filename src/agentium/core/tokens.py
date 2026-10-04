from __future__ import annotations

from typing import Callable, Optional

_custom_tokenizer: Optional[Callable[[str], int]] = None


def set_tokenizer(tokenizer_fn: Optional[Callable[[str], int]]) -> None:
    """Set custom pluggable tokenizer function."""
    global _custom_tokenizer
    _custom_tokenizer = tokenizer_fn


def estimate_tokens(text: str) -> int:
    """Estimate token count for a given text.
    By default uses a zero-dependency length-based heuristic (len(text) // 4).
    If a custom tokenizer has been registered with set_tokenizer(), it delegates to it.
    """
    if not text:
        return 0
    if _custom_tokenizer is not None:
        try:
            return _custom_tokenizer(text)
        except Exception:
            # Fall back safely to standard heuristic
            pass
    return max(1, len(text) // 4)
