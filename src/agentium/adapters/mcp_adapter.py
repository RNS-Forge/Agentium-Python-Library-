"""MCP (Model Context Protocol) Adapter for Agentium v2.

Exports Agentium tool registries and decorated tools as standard MCP tools,
preserving effect tags ('read', 'write', 'destructive') for downstream policy enforcement.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .._meta import PACKAGE_NAME
from .plain import get_tool_registry

try:
    import mcp as _raw_mcp
except ImportError:
    _raw_mcp = None  # type: ignore


def _ensure_installed() -> None:
    if _raw_mcp is None:
        raise ImportError(
            f"MCP adapter requires the 'mcp' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[mcp]'"
        )


raw = _raw_mcp


def tool_to_mcp_dict(tool_obj: Any) -> Dict[str, Any]:
    """Convert an Agentium tool or callable into a standard MCP tool descriptor dictionary."""
    name = getattr(tool_obj, "name", getattr(tool_obj, "__name__", "unnamed_tool"))
    doc = getattr(tool_obj, "doc", getattr(tool_obj, "__doc__", "")) or ""
    effect = getattr(tool_obj, "effect", getattr(tool_obj, "__agentium_tool_effect__", "read"))
    schema = getattr(tool_obj, "parameters_schema", None) or {
        "type": "object",
        "properties": {},
    }

    return {
        "name": name,
        "description": doc.strip(),
        "inputSchema": schema,
        "metadata": {
            "effect": effect,
            "agentium_managed": True,
        },
    }


def export_registry_to_mcp(registry: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Export all registered tools in an Agentium ToolRegistry as MCP tool descriptors."""
    reg = registry or get_tool_registry()
    tools: List[Dict[str, Any]] = []

    if hasattr(reg, "list_all"):
        for _, tool_def in reg.list_all().items():
            tools.append(tool_to_mcp_dict(tool_def))
    elif hasattr(reg, "list_tools"):
        for tool_name in reg.list_tools():
            tool_obj = reg.get(tool_name)
            if tool_obj:
                tools.append(tool_to_mcp_dict(tool_obj))
    return tools
