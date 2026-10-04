"""F6: Compaction Soak Test Harness."""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol

from .guard import guard_compaction, reinject
from .store import PinStore


class CompactorProtocol(Protocol):
    def __call__(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...


class TruncateCompactor:
    """Drops the oldest N non-system messages."""

    def __init__(self, drop_count: int = 4) -> None:
        self.drop_count = drop_count

    def __call__(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(messages) <= self.drop_count:
            return copy.deepcopy(messages)
        return copy.deepcopy(messages[self.drop_count:])


class LastNCompactor:
    """Retains only the last N messages."""

    def __init__(self, keep_last: int = 5) -> None:
        self.keep_last = keep_last

    def __call__(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return copy.deepcopy(messages[-self.keep_last:])


class StubSummarizer:
    """Replaces older messages with a summary string."""

    def __init__(self, keep_recent: int = 3) -> None:
        self.keep_recent = keep_recent

    def __call__(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(messages) <= self.keep_recent:
            return copy.deepcopy(messages)
        summarized = messages[:-self.keep_recent]
        recent = messages[-self.keep_recent:]
        summary_msg = {
            "role": "system",
            "content": f"[CONVERSATION SUMMARY: Processed {len(summarized)} prior turns successfully]",
        }
        return [summary_msg] + copy.deepcopy(recent)


@dataclass
class SoakReport:
    turns: int
    compactions_triggered: int
    pins_injected: int
    pins_lost_before_repair: int
    pins_survived: int
    all_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_text(self) -> str:
        status = "PASSED" if self.all_passed else "FAILED"
        return (
            f"Compaction Soak Test Report: {status}\n"
            f"  Turns Simulated             : {self.turns}\n"
            f"  Compactions Triggered       : {self.compactions_triggered}\n"
            f"  Pins Injected               : {self.pins_injected}\n"
            f"  Pins Lost Before Repair     : {self.pins_lost_before_repair}\n"
            f"  Pins Survived (After Repair): {self.pins_survived}\n"
            f"  Integrity Preserved         : {self.all_passed}"
        )


def assert_pins_survive(messages: List[Dict[str, Any]], pin_store: PinStore) -> None:
    """Raise AssertionError if any active pin in pin_store is missing from messages."""
    text_corpus = " ".join(str(m.get("content", "")) for m in messages)
    active = pin_store.active_pins()
    for pin in active:
        key_line = f"[{pin.key}]: {pin.text}"
        if key_line not in text_corpus and pin.text not in text_corpus:
            raise AssertionError(
                f"Pin survival failure: active pin '{pin.key}' ('{pin.text[:30]}...') "
                f"was lost and not present in messages."
            )


def soak(
    compactor: Optional[CompactorProtocol] = None,
    num_turns: int = 20,
    pin_interval: int = 3,
    compaction_threshold: int = 8,
    agent_callable: Optional[Callable[[List[Dict[str, Any]]], Dict[str, Any]]] = None,
) -> SoakReport:
    """Run simulated multi-turn conversation exercising compaction and pin preservation."""
    actual_compactor = compactor or LastNCompactor(keep_last=5)
    pin_store = PinStore()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": "You are a dependable long-running agent."}
    ]

    compactions_count = 0
    total_pins_lost = 0
    total_pins_injected = 0

    for turn in range(1, num_turns + 1):
        # 1. User message
        messages.append({"role": "user", "content": f"User prompt turn {turn}: please process request."})

        # 2. Inject pin periodically
        if turn % pin_interval == 0:
            pin_key = f"goal_{turn // pin_interval}"
            pin_text = f"Crucial directive registered at turn {turn}: enforce SLA tier 1"
            pin_store.add(pin_key, pin_text)
            total_pins_injected += 1
            # Re-inject current pins
            messages = reinject(messages, pin_store)

        # 3. Agent response (mock or callable)
        if agent_callable:
            resp = agent_callable(messages)
            messages.append(resp)
        else:
            messages.append({"role": "assistant", "content": f"Acknowledged turn {turn} response."})

        # 4. Compaction trigger
        if len(messages) >= compaction_threshold:
            compactions_count += 1
            compacted = actual_compactor(messages)
            repaired, lost, restored = guard_compaction(messages, compacted, pin_store)
            total_pins_lost += lost
            messages = repaired

            # Verify integrity
            assert_pins_survive(messages, pin_store)

    # Final assertion at end of run
    assert_pins_survive(messages, pin_store)
    active_count = len(pin_store.active_pins())

    return SoakReport(
        turns=num_turns,
        compactions_triggered=compactions_count,
        pins_injected=total_pins_injected,
        pins_lost_before_repair=total_pins_lost,
        pins_survived=active_count,
        all_passed=True,
    )
