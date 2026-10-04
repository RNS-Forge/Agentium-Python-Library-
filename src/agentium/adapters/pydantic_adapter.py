"""Pydantic Adapter for Agentium v2.

Provides schema extraction, type validation, and data parsing for tool arguments and handoffs.
"""
from __future__ import annotations

from typing import Any, Dict, Type

from .._meta import PACKAGE_NAME

try:
    import pydantic as _raw_pydantic
    from pydantic import BaseModel, ValidationError
except ImportError:
    _raw_pydantic = None  # type: ignore
    BaseModel = object  # type: ignore
    ValidationError = Exception  # type: ignore


def _ensure_installed() -> None:
    if _raw_pydantic is None:
        raise ImportError(
            f"Pydantic adapter requires the 'pydantic' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[pydantic]'"
        )


raw = _raw_pydantic


def validate(model_cls: Type[Any], data: Any) -> Any:
    """Validate data against a Pydantic model class."""
    _ensure_installed()
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    elif hasattr(model_cls, "parse_obj"):
        return model_cls.parse_obj(data)
    return model_cls(**data if isinstance(data, dict) else {"value": data})


def to_schema(model_cls: Type[Any]) -> Dict[str, Any]:
    """Extract standard JSON Schema from a Pydantic model class."""
    _ensure_installed()
    if hasattr(model_cls, "model_json_schema"):
        return model_cls.model_json_schema()
    elif hasattr(model_cls, "schema"):
        return model_cls.schema()
    raise TypeError(f"Object {model_cls} does not appear to be a Pydantic model class")


def dump(instance: Any) -> Dict[str, Any]:
    """Serialize a Pydantic model instance to a standard Python dict."""
    _ensure_installed()
    if hasattr(instance, "model_dump"):
        return instance.model_dump()
    elif hasattr(instance, "dict"):
        return instance.dict()
    return dict(instance)
