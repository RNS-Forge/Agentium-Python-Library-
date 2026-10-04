"""F5: Pin Data Model and PinStore."""
from __future__ import annotations

import copy
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.hashing import canonical_json, sha256_hex


@dataclass
class Pin:
    id: str
    key: str
    text: str
    source: str = "system"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    superseded_by: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.superseded_by is None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Pin:
        return cls(
            id=data["id"],
            key=data["key"],
            text=data["text"],
            source=data.get("source", "system"),
            created_at=data.get("created_at", ""),
            metadata=data.get("metadata", {}),
            superseded_by=data.get("superseded_by"),
        )


class PinStore:
    """In-memory per-run pin store with audit preservation and deterministic rendering."""

    def __init__(self, run_id: Optional[str] = None) -> None:
        self.run_id = run_id or str(uuid.uuid4())
        self._pins: Dict[str, Pin] = {}  # id -> Pin
        self._key_to_latest_id: Dict[str, str] = {}  # key -> id

    def add(
        self,
        key: str,
        text: str,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Pin:
        """Add a pin. If a pin with the same key exists, mark previous as superseded."""
        pin_id = f"pin_{uuid.uuid4().hex[:12]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        if key in self._key_to_latest_id:
            old_id = self._key_to_latest_id[key]
            old_pin = self._pins[old_id]
            # Supersede old pin
            self._pins[old_id] = Pin(
                id=old_pin.id,
                key=old_pin.key,
                text=old_pin.text,
                source=old_pin.source,
                created_at=old_pin.created_at,
                metadata=old_pin.metadata,
                superseded_by=pin_id,
            )

        new_pin = Pin(
            id=pin_id,
            key=key,
            text=text,
            source=source,
            created_at=now_ts,
            metadata=copy.deepcopy(metadata or {}),
            superseded_by=None,
        )
        self._pins[pin_id] = new_pin
        self._key_to_latest_id[key] = pin_id
        return new_pin

    def get(self, key: str) -> Optional[Pin]:
        """Get the current active pin for a key, or None if not found."""
        pin_id = self._key_to_latest_id.get(key)
        if pin_id and self._pins[pin_id].is_active:
            return self._pins[pin_id]
        return None

    def get_by_id(self, pin_id: str) -> Optional[Pin]:
        return self._pins.get(pin_id)

    def active_pins(self) -> List[Pin]:
        """Return all active (non-superseded) pins, sorted deterministically by (created_at, id)."""
        active = [p for p in self._pins.values() if p.is_active]
        return sorted(active, key=lambda p: (p.created_at, p.id))

    def all_pins(self) -> List[Pin]:
        """Return all pins including superseded audit records."""
        return sorted(self._pins.values(), key=lambda p: (p.created_at, p.id))

    def render(self) -> str:
        """Deterministic formatted string of all active pins."""
        active = self.active_pins()
        if not active:
            return ""
        lines = ["[ACTIVE CONTEXT PINS]"]
        for p in active:
            lines.append(f"- [{p.key}]: {p.text}")
        return "\n".join(lines)

    def fingerprint(self) -> str:
        """Canonical SHA-256 hash of active pins representation."""
        payload = [{"key": p.key, "text": p.text} for p in self.active_pins()]
        return sha256_hex(payload)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "pins": [p.to_dict() for p in self.all_pins()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PinStore:
        store = cls(run_id=data.get("run_id"))
        for p_data in data.get("pins", []):
            pin = Pin.from_dict(p_data)
            store._pins[pin.id] = pin
            if pin.is_active:
                store._key_to_latest_id[pin.key] = pin.id
        return store
