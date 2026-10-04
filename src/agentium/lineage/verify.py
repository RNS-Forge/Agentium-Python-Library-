"""Verifier Registry and Built-in Grounding Verifiers."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional, Tuple

from .claims import Claim, EvidenceRef


_VERIFIER_REGISTRY: Dict[str, Callable[..., Tuple[bool, Optional[str], Optional[EvidenceRef]]]] = {}


def register_verifier(name: str, fn: Callable[..., Tuple[bool, Optional[str], Optional[EvidenceRef]]]) -> None:
    _VERIFIER_REGISTRY[name] = fn


def get_verifier(name: str) -> Optional[Callable[..., Tuple[bool, Optional[str], Optional[EvidenceRef]]]]:
    return _VERIFIER_REGISTRY.get(name)


def verifier(name: str):
    """Decorator to register a verifier function."""
    def decorator(fn: Callable[..., Tuple[bool, Optional[str], Optional[EvidenceRef]]]):
        register_verifier(name, fn)
        return fn
    return decorator


class JsonFieldExtractor:
    """Built-in verifier that checks if a JSON payload matches expected field values."""

    def __init__(self, key_path: str, expected_value: Any) -> None:
        self.key_path = key_path
        self.expected_value = expected_value

    def verify(self, payload: Any, source_id: str = "tool_call") -> Tuple[bool, Optional[str], Optional[EvidenceRef]]:
        data = payload
        if isinstance(payload, str):
            try:
                data = json.loads(payload)
            except Exception as e:
                return False, f"Payload is not valid JSON: {e}", None

        # Navigate key_path (e.g. "user.profile.status")
        segments = self.key_path.split(".")
        curr: Any = data
        for seg in segments:
            if isinstance(curr, dict) and seg in curr:
                curr = curr[seg]
            else:
                return False, f"Key segment '{seg}' not found in payload.", None

        if curr == self.expected_value:
            ev = EvidenceRef(
                source_type="tool_call",
                source_id=source_id,
                excerpt=f"Matched {self.key_path} == {self.expected_value}",
            )
            return True, None, ev

        return False, f"Value mismatch at '{self.key_path}': expected {self.expected_value}, got {curr}", None


# Register default json extractor verifier
@verifier(name="json_match")
def json_match_verifier(
    claim: Claim,
    payload: Any,
    field_path: str,
    expected_val: Any,
    source_id: str = "tool_result",
) -> Tuple[bool, Optional[str], Optional[EvidenceRef]]:
    extractor = JsonFieldExtractor(field_path, expected_val)
    return extractor.verify(payload, source_id=source_id)
