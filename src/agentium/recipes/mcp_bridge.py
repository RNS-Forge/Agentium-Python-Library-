"""Recipe R25: mcp_bridge (mcp + ToolRegistry + ActionGate).

Exposes Agentium tools over the Model Context Protocol (MCP) while preserving
effect tags ('read', 'write', 'destructive') and enforcing ActionGate safety policies
before executing MCP tool invocations.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from .._meta import PACKAGE_NAME
from ..adapters.mcp_adapter import export_registry_to_mcp
from ..adapters.plain import ToolRegistry, get_tool_registry
from ..core.events import EventType
from ..core.run import get_current_run
from ..lineage.gate import ActionBlockedError, ActionGate


class McpBridge:
    """Bridge exposing Agentium ToolRegistry over standard MCP tool protocols."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        action_gate: Optional[ActionGate] = None,
    ) -> None:
        self.registry = registry or get_tool_registry()
        self.action_gate = action_gate or ActionGate(mode="enforce")

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools formatted as standard MCP tool descriptors."""
        return export_registry_to_mcp(self.registry)

    def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        human_confirmed: bool = False,
    ) -> Any:
        """Dispatch a tool call through MCP with ActionGate policy verification."""
        tool_obj = self.registry.get(name)
        if not tool_obj:
            raise KeyError(f"Tool '{name}' not found in registry.")

        effect = getattr(tool_obj, "__agentium_tool_effect__", getattr(tool_obj, "effect", "read"))
        args = arguments or {}

        # 1. ActionGate Policy Check
        allowed, reason = self.action_gate.evaluate(
            tool_name=name,
            effect=effect,
            arguments=args,
            human_confirmed=human_confirmed,
        )

        if not allowed:
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.ACTION_GATE_BLOCK,
                    {"tool_name": name, "effect": effect, "reason": reason, "channel": "mcp"},
                )
            raise ActionBlockedError(f"MCP tool call '{name}' blocked by ActionGate: {reason}")

        # 2. Execute tool
        ctx = get_current_run()
        if ctx and ctx.event_writer:
            ctx.event_writer.write(
                EventType.TOOL_CALL,
                {"tool_name": name, "effect": effect, "channel": "mcp"},
            )

        try:
            fn = getattr(tool_obj, "fn", tool_obj)
            res = fn(**args) if isinstance(args, dict) else fn(args)
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": name, "effect": effect, "status": "success", "channel": "mcp"},
                )
            return res
        except Exception as exc:
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": name, "effect": effect, "status": "error", "error": str(exc), "channel": "mcp"},
                )
            raise

    async def call_tool_async(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        human_confirmed: bool = False,
    ) -> Any:
        """Async twin: Dispatch a tool call through MCP with ActionGate policy verification."""
        tool_obj = self.registry.get(name)
        if not tool_obj:
            raise KeyError(f"Tool '{name}' not found in registry.")

        fn = getattr(tool_obj, "fn", tool_obj)
        if asyncio.iscoroutinefunction(fn):
            effect = getattr(tool_obj, "__agentium_tool_effect__", getattr(tool_obj, "effect", "read"))
            args = arguments or {}
            allowed, reason = self.action_gate.evaluate(
                tool_name=name,
                effect=effect,
                arguments=args,
                human_confirmed=human_confirmed,
            )
            if not allowed:
                raise ActionBlockedError(f"MCP tool call '{name}' blocked by ActionGate: {reason}")
            return await fn(**args) if isinstance(args, dict) else await fn(args)

        return await asyncio.to_thread(
            self.call_tool,
            name=name,
            arguments=arguments,
            human_confirmed=human_confirmed,
        )


def mcp_bridge(
    registry: Optional[ToolRegistry] = None,
    action_gate: Optional[ActionGate] = None,
) -> McpBridge:
    """Create an McpBridge exposing Agentium tools with ActionGate preservation."""
    return McpBridge(registry=registry, action_gate=action_gate)


async def mcp_bridge_async(
    registry: Optional[ToolRegistry] = None,
    action_gate: Optional[ActionGate] = None,
) -> McpBridge:
    """Async twin: Create an McpBridge exposing Agentium tools with ActionGate preservation."""
    return await asyncio.to_thread(mcp_bridge, registry=registry, action_gate=action_gate)
