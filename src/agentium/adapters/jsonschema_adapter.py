"""JSONSchema Adapter for Agentium v2.

Provides standard JSON Schema validation for tool payloads and handoff verification.
"""
from __future__ import annotations

from typing import Any, Dict

from .._meta import PACKAGE_NAME

try:
    import jsonschema as _raw_jsonschema
    from jsonschema.exceptions import ValidationError
except ImportError:
    _raw_jsonschema = None  # type: ignore
    ValidationError = Exception  # type: ignore


def _ensure_installed() -> None:
    if _raw_jsonschema is None:
        raise ImportError(
            f"JSONSchema adapter requires the 'jsonschema' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[jsonschema]'"
        )


raw = _raw_jsonschema


def validate(instance: Any, schema: Dict[str, Any]) -> None:
    """Validate an instance against a JSON schema. Raises jsonschema.ValidationError on failure."""
    _ensure_installed()
    _raw_jsonschema.validate(instance=instance, schema=schema)


def is_valid(instance: Any, schema: Dict[str, Any]) -> bool:
    """Return True if instance is valid against schema, False otherwise."""
    _ensure_installed()
    validator_cls = _raw_jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)
    return validator.is_valid(instance)
