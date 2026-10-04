"""Recipe R15: smart_compact (tiktoken + F5 pin store + F6 compaction guard).

Token-accurate context compaction using tiktoken that bounds conversation token
length while strictly guaranteeing all active context pins are preserved and re-injected.
"""
from __future__ import annotations

import asyncio
import copy
from typing import Any, Dict, List, Optional, Tuple

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run
from ..pin.guard import guard_compaction, reinject
from ..pin.store import PinStore


def smart_compact(
    messages: List[Dict[str, Any]],
    pin_store: PinStore,
    max_tokens: int = 2000,
    model_or_encoding: str = "cl100k_base",
    keep_last_n: int = 4,
) -> Tuple[List[Dict[str, Any]], int, int]:
    """Compact message history to fit within max_tokens while guaranteeing pin integrity.

    Args:
        messages: List of conversation message dictionaries.
        pin_store: PinStore maintaining active pins.
        max_tokens: Maximum allowed token budget.
        model_or_encoding: Tiktoken model name or encoding name.
        keep_last_n: Minimum number of recent messages to preserve intact.

    Returns:
        (compacted_messages, tokens_before, tokens_after)
    """
    try:
        from ..adapters import tiktoken_adapter
    except ImportError as exc:
        raise ImportError(
            f"Recipe 'smart_compact' requires 'tiktoken'. "
            f"Install via: pip install '{PACKAGE_NAME}[tiktoken]'"
        ) from exc

    def _calc_tokens(msgs: List[Dict[str, Any]]) -> int:
        joined = " ".join(str(m.get("content", "")) for m in msgs)
        return tiktoken_adapter.count_tokens(joined, model_or_encoding=model_or_encoding)

    tokens_before = _calc_tokens(messages)
    if tokens_before <= max_tokens:
        # Guarantee pins are injected even if no compaction needed
        final_msgs = reinject(messages, pin_store)
        return final_msgs, tokens_before, _calc_tokens(final_msgs)

    # Separate system messages, recent messages, and candidate history
    system_msgs: List[Dict[str, Any]] = [m for m in messages if m.get("role") == "system"]
    non_system: List[Dict[str, Any]] = [m for m in messages if m.get("role") != "system"]

    if len(non_system) <= keep_last_n:
        compacted = copy.deepcopy(messages)
    else:
        # Keep the most recent keep_last_n messages
        tail_msgs = non_system[-keep_last_n:]
        compacted = copy.deepcopy(system_msgs) + tail_msgs

    # Run through compaction guard to verify and re-inject pins
    repaired, lost, restored = guard_compaction(
        original_messages=messages,
        compacted_messages=compacted,
        pin_store=pin_store,
    )

    tokens_after = _calc_tokens(repaired)

    ctx = get_current_run()
    if ctx and ctx.event_writer:
        ctx.event_writer.write(
            EventType.COMPACTION,
            {
                "recipe": "smart_compact",
                "tokens_before": tokens_before,
                "tokens_after": tokens_after,
                "max_tokens": max_tokens,
                "pins_restored": restored,
            },
        )

    return repaired, tokens_before, tokens_after


async def smart_compact_async(
    messages: List[Dict[str, Any]],
    pin_store: PinStore,
    max_tokens: int = 2000,
    model_or_encoding: str = "cl100k_base",
    keep_last_n: int = 4,
) -> Tuple[List[Dict[str, Any]], int, int]:
    """Async twin: Compact message history to fit within max_tokens while guaranteeing pin integrity."""
    return await asyncio.to_thread(
        smart_compact,
        messages=messages,
        pin_store=pin_store,
        max_tokens=max_tokens,
        model_or_encoding=model_or_encoding,
        keep_last_n=keep_last_n,
    )
