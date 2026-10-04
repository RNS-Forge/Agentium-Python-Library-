"""Plugin discovery and registration via importlib.metadata entry points."""
from __future__ import annotations

import importlib.metadata
import sys
from typing import Any, Dict, Optional

from .._meta import PLUGIN_ENTRYPOINT_GROUP

_REGISTERED_PLUGINS: Dict[str, Any] = {}


def discover_plugins(group: str = PLUGIN_ENTRYPOINT_GROUP) -> Dict[str, Any]:
    """Discover and load external third-party plugins declared under entry-point group."""
    try:
        eps = importlib.metadata.entry_points()
        # In Python 3.10+, entry_points(group=...) is standard
        if hasattr(eps, "select"):
            selected = eps.select(group=group)
        elif isinstance(eps, dict):
            selected = eps.get(group, [])
        else:
            selected = [ep for ep in eps if getattr(ep, "group", None) == group]

        for ep in selected:
            try:
                plugin_impl = ep.load()
                _REGISTERED_PLUGINS[ep.name] = plugin_impl
            except Exception:
                pass
    except Exception:
        pass
    return dict(_REGISTERED_PLUGINS)


def get_plugin(name: str) -> Optional[Any]:
    """Retrieve a discovered or manually registered plugin by name."""
    if name not in _REGISTERED_PLUGINS:
        discover_plugins()
    return _REGISTERED_PLUGINS.get(name)


def register_plugin(name: str, plugin_impl: Any) -> None:
    """Manually register an in-memory plugin."""
    _REGISTERED_PLUGINS[name] = plugin_impl


def list_plugins() -> Dict[str, Any]:
    """List all currently loaded plugins."""
    if not _REGISTERED_PLUGINS:
        discover_plugins()
    return dict(_REGISTERED_PLUGINS)
