"""F10: Speculative Read-Only Tool Prefetch (Experimental).

Strictly opt-in acceleration engine using Markov transition prediction
and TTL-cached execution strictly confined to read-only tools.
"""
from __future__ import annotations

import collections
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from ..adapters.plain import get_tool_registry
from ..core.events import EventType, EventWriter
from ..core.hashing import canonical_json, sha256_hex
from ..core.run import get_current_run


@dataclass
class CacheEntry:
    key: str
    result: Any
    created_at: float
    ttl: float

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl


class ToolPredictor:
    """Predicts next tool call based on observed Markov transition frequencies."""

    def __init__(self) -> None:
        # transition_counts[current_tool][next_tool] = count
        self.transitions: Dict[str, Dict[str, int]] = collections.defaultdict(lambda: collections.defaultdict(int))
        self.last_tool: Optional[str] = None

    def record_transition(self, tool_name: str) -> None:
        if self.last_tool is not None:
            self.transitions[self.last_tool][tool_name] += 1
        self.last_tool = tool_name

    def predict_next(self, current_tool: str, min_confidence: float = 0.4) -> Optional[str]:
        candidates = self.transitions.get(current_tool)
        if not candidates:
            return None
        total = sum(candidates.values())
        best_tool, best_count = max(candidates.items(), key=lambda item: item[1])
        if (best_count / total) >= min_confidence:
            return best_tool
        return None


class PrefetchManager:
    """Orchestrator for speculative tool prefetching."""

    def __init__(
        self,
        enabled: Optional[bool] = None,
        max_in_flight: int = 3,
        ttl_seconds: float = 60.0,
        max_wasted_per_run: int = 5,
        hit_rate_threshold: float = 0.3,
        min_eval_calls: int = 5,
        event_writer: Optional[EventWriter] = None,
    ) -> None:
        # Strictly opt-in: check argument, then env var
        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = os.environ.get("AGENTIUM_EXPERIMENTAL_PREFETCH") in ("1", "true", "yes")

        self.max_in_flight = max_in_flight
        self.ttl_seconds = ttl_seconds
        self.max_wasted_per_run = max_wasted_per_run
        self.hit_rate_threshold = hit_rate_threshold
        self.min_eval_calls = min_eval_calls
        self.event_writer = event_writer

        self.predictor = ToolPredictor()
        self.cache: Dict[str, CacheEntry] = {}
        self.in_flight: Set[str] = set()

        # Circuit breaker metrics
        self.prefetched_count = 0
        self.hit_count = 0
        self.wasted_count = 0
        self.circuit_broken = False

    def _get_writer(self) -> Optional[EventWriter]:
        if self.event_writer is not None:
            return self.event_writer
        ctx = get_current_run()
        return ctx.event_writer if ctx is not None else None

    def _make_key(self, tool_name: str, kwargs: Dict[str, Any]) -> str:
        payload = {"tool": tool_name, "kwargs": kwargs}
        return sha256_hex(payload)

    def is_active(self) -> bool:
        return self.enabled and not self.circuit_broken

    def maybe_prefetch(
        self,
        tool_name: str,
        tool_fn: Callable[..., Any],
        effect: str,
        kwargs: Dict[str, Any],
    ) -> bool:
        """Attempt to speculatively prefetch a tool invocation.

        CRITICAL INVARIANT: NEVER prefetch non-read tools.
        """
        if not self.is_active():
            return False

        # Invariant check: MUST be read-only
        if effect.lower() != "read":
            return False

        if len(self.in_flight) >= self.max_in_flight:
            return False

        key = self._make_key(tool_name, kwargs)
        if key in self.cache and not self.cache[key].is_expired:
            return False  # Already cached

        writer = self._get_writer()
        if writer:
            writer.write(
                EventType.PREFETCH_ATTEMPT,
                {"tool_name": tool_name, "effect": effect, "arguments": kwargs},
            )

        try:
            self.in_flight.add(key)
            # Execute speculation synchronously for now (or thread pool in async)
            result = tool_fn(**kwargs)
            self.cache[key] = CacheEntry(
                key=key,
                result=result,
                created_at=time.time(),
                ttl=self.ttl_seconds,
            )
            self.prefetched_count += 1
            return True
        except Exception:
            return False
        finally:
            self.in_flight.discard(key)

    def get_or_record_usage(
        self,
        tool_name: str,
        kwargs: Dict[str, Any],
    ) -> Tuple[bool, Any]:
        """Check cache upon actual tool call. Returns (is_hit, cached_result_or_None)."""
        # Always train predictor on actual tool calls
        self.predictor.record_transition(tool_name)

        if not self.is_active():
            return False, None

        key = self._make_key(tool_name, kwargs)
        writer = self._get_writer()

        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired:
                self.hit_count += 1
                del self.cache[key]  # Consume cached result
                if writer:
                    writer.write(
                        EventType.PREFETCH_RESULT,
                        {"tool_name": tool_name, "outcome": "hit", "hit_count": self.hit_count},
                    )
                return True, entry.result
            else:
                # Expired
                del self.cache[key]

        return False, None

    def reap_wasted(self) -> None:
        """Sweep expired cache entries and evaluate circuit breaker."""
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if (now - v.created_at) > v.ttl]
        for k in expired_keys:
            del self.cache[k]
            self.wasted_count += 1

        writer = self._get_writer()
        if expired_keys and writer:
            writer.write(
                EventType.PREFETCH_RESULT,
                {"outcome": "wasted", "wasted_count": self.wasted_count},
            )

        # Check circuit breaker conditions
        total_eval = self.hit_count + self.wasted_count
        if total_eval >= self.min_eval_calls:
            hit_rate = self.hit_count / total_eval
            if hit_rate < self.hit_rate_threshold:
                self.circuit_broken = True

        if self.wasted_count >= self.max_wasted_per_run:
            self.circuit_broken = True
