from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from typing import Any


def _normalize_obj(obj: Any) -> Any:
    """Normalize object recursively:
    - Strings & dict keys: Unicode NFC normalization
    - Integer-valued floats: normalized to int (1.0 -> 1)
    - Booleans preserved as bool
    - NaN and Infinite floats rejected with ValueError
    """
    if isinstance(obj, bool):
        return obj
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError(f"Canonical JSON does not allow NaN or Infinity: {obj}")
        if obj.is_integer():
            return int(obj)
        return obj
    elif isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    elif isinstance(obj, dict):
        return {
            unicodedata.normalize("NFC", str(k)): _normalize_obj(v)
            for k, v in sorted(obj.items(), key=lambda item: unicodedata.normalize("NFC", str(item[0])))
        }
    elif isinstance(obj, (list, tuple)):
        return [_normalize_obj(item) for item in obj]
    elif isinstance(obj, (set, frozenset)):
        # Normalize and sort set elements
        normalized_items = [_normalize_obj(item) for item in obj]
        try:
            return sorted(normalized_items)
        except TypeError:
            # Fallback sort by string representation if items not directly comparable
            return sorted(normalized_items, key=lambda x: canonical_json(x))
    return obj


def canonical_json(obj: Any) -> str:
    """Serialize object to canonical JSON string.
    Note: This is an internal Agentium deterministic serialization format,
    NOT RFC 8785 (JCS).
    Properties:
    - Unicode NFC on all strings and dict keys
    - Keys sorted lexicographically
    - Compact separators (',', ':')
    - ensure_ascii=False
    - allow_nan=False (raises ValueError on NaN/Inf)
    - Integer floats normalized to int (1.0 == 1)
    """
    normalized = _normalize_obj(obj)
    return json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_hex(data: Any) -> str:
    """Generate SHA-256 hexadecimal hash from string, bytes, or canonical JSON object."""
    if isinstance(data, str):
        raw_bytes = unicodedata.normalize("NFC", data).encode("utf-8")
    elif isinstance(data, bytes):
        raw_bytes = data
    else:
        raw_bytes = canonical_json(data).encode("utf-8")
    return hashlib.sha256(raw_bytes).hexdigest()
