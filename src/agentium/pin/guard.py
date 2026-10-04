"""F5: Pin Re-injection and Compaction Guard."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple, Union

from ..core.events import EventType, EventWriter
from ..core.run import get_current_run
from .store import PinStore


PIN_BLOCK_HEADER = "[ACTIVE CONTEXT PINS]"


def _is_pin_message(msg: Dict[str, Any]) -> bool:
    content = str(msg.get("content", ""))
    return PIN_BLOCK_HEADER in content


def reinject(
    messages: List[Dict[str, Any]],
    pin_store: PinStore,
    position: str = "end",
    role: str = "system",
) -> List[Dict[str, Any]]:
    """Idempotently and non-destructively inject active pins into messages.

    Args:
        messages: List of message dictionaries (e.g. {"role": "...", "content": "..."})
        pin_store: PinStore containing active pins
        position: "end" (append/replace at tail) or "start" (prepend/replace at head)
        role: Message role for the pin container (default "system")

    Returns:
        New list of messages with active pins injected.
    """
    rendered = pin_store.render()
    if not rendered:
        # No active pins; return copy without modifying
        return [copy.deepcopy(m) for m in messages]

    result = [copy.deepcopy(m) for m in messages]

    if position == "end":
        # Check if last message is already a pin message
        if result and _is_pin_message(result[-1]):
            if result[-1].get("content") == rendered:
                return result  # Idempotent no-op
            # Update last pin message with current pins
            result[-1]["content"] = rendered
            return result
        # Check if any message contains older pin block; remove to prevent duplicates
        result = [m for m in result if not _is_pin_message(m)]
        result.append({"role": role, "content": rendered})
        return result

    elif position == "start":
        # Check if first message is already a pin message
        if result and _is_pin_message(result[0]):
            if result[0].get("content") == rendered:
                return result  # Idempotent no-op
            result[0]["content"] = rendered
            return result
        result = [m for m in result if not _is_pin_message(m)]
        result.insert(0, {"role": role, "content": rendered})
        return result

    else:
        raise ValueError(f"Unsupported reinject position '{position}'. Expected 'end' or 'start'.")


def guard_compaction(
    original_messages: List[Dict[str, Any]],
    compacted_messages: List[Dict[str, Any]],
    pin_store: PinStore,
    event_writer: Optional[EventWriter] = None,
    position: str = "end",
    role: str = "system",
) -> Tuple[List[Dict[str, Any]], int, int]:
    """Verify active pins survive compaction, re-injecting them if dropped.

    Returns:
        (repaired_messages, pins_lost, pins_restored)
    """
    active_pins = pin_store.active_pins()
    if not active_pins:
        return [copy.deepcopy(m) for m in compacted_messages], 0, 0

    # Search for pins in compacted_messages
    compacted_text = " ".join(str(m.get("content", "")) for m in compacted_messages)

    pins_lost = 0
    for p in active_pins:
        # Check if either exact pin key/text pattern or rendered line survived
        key_signature = f"[{p.key}]: {p.text}"
        if key_signature not in compacted_text and p.text not in compacted_text:
            pins_lost += 1

    # Re-inject active pins into compacted messages
    repaired_messages = reinject(compacted_messages, pin_store, position=position, role=role)
    pins_restored = pins_lost

    # Emit audit event if event_writer provided or active run context exists
    active_writer = event_writer
    run_ctx = get_current_run()
    if active_writer is None and run_ctx is not None:
        active_writer = run_ctx.event_writer

    if active_writer is not None:
        active_writer.write(
            EventType.COMPACTION,
            {
                "original_message_count": len(original_messages),
                "compacted_message_count": len(compacted_messages),
                "repaired_message_count": len(repaired_messages),
                "pins_active_count": len(active_pins),
                "pins_lost": pins_lost,
                "pins_restored": pins_restored,
            },
        )

    return repaired_messages, pins_lost, pins_restored
