"""Recipe R45: mcp_safe_tools (mcp + tenacity + pybreaker + ActionGate).

Exposes Model Context Protocol (MCP) tools bolstered by automated retries and circuit breakers,
while strictly preserving Agentium ActionGate governance over destructive side-effects.
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


class McpSafeToolsBridge:
    """Resilient MCP Bridge with built-in retries, circuit breakers, and ActionGate safety."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        action_gate: Optional[ActionGate] = None,
        max_attempts: int = 3,
        fail_max: int = 5,
        reset_timeout: int = 60,
    ) -> None:
        self.registry = registry or get_tool_registry()
        self.action_gate = action_gate or ActionGate(mode="enforce")
        self.max_attempts = max_attempts
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self._breakers: Dict[str, Any] = {}

    def _get_breaker(self, name: str) -> Any:
        try:
            import pybreaker
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'mcp_safe_tools' requires 'pybreaker'. "
                f"Install via: pip install '{PACKAGE_NAME}[pybreaker]'"
            ) from exc

        if name not in self._breakers:
            self._breakers[name] = pybreaker.CircuitBreaker(
                fail_max=self.fail_max,
                reset_timeout=self.reset_timeout,
                name=f"mcp_{name}",
            )
        return self._breakers[name]

    def list_tools(self) -> List[Dict[str, Any]]:
        """List registered tools formatted as standard MCP tool descriptors."""
        return export_registry_to_mcp(self.registry)

    def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        human_confirmed: bool = False,
    ) -> Any:
        """Dispatch tool call through MCP with retry, breaker, and ActionGate gating."""
        tool_obj = self.registry.get(name)
        if not tool_obj:
            raise KeyError(f"MCP tool '{name}' not found.")

        effect = getattr(tool_obj, "__agentium_tool_effect__", getattr(tool_obj, "effect", "read"))
        args = arguments or {}

        # 1. ActionGate Evaluation
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
                    {"tool_name": name, "effect": effect, "reason": reason, "channel": "mcp_safe"},
                )
            raise ActionBlockedError(f"MCP tool '{name}' blocked by ActionGate: {reason}")

        # 2. Resilient Execution with Tenacity and PyBreaker
        try:
            import tenacity
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'mcp_safe_tools' requires 'tenacity'. "
                f"Install via: pip install '{PACKAGE_NAME}[tenacity]'"
            ) from exc

        breaker = self._get_breaker(name)
        retryer = tenacity.Retrying(
            stop=tenacity.stop_after_attempt(self.max_attempts),
            wait=tenacity.wait_exponential(multiplier=0.1, min=0.1, max=1.0),
            reraise=True,
        )

        ctx = get_current_run()
        if ctx and ctx.event_writer:
            ctx.event_writer.write(
                EventType.TOOL_CALL,
                {"tool_name": name, "effect": effect, "recipe": "mcp_safe_tools"},
            )

        fn = getattr(tool_obj, "fn", tool_obj)

        def _exec():
            return fn(**args) if isinstance(args, dict) else fn(args)

        for attempt in retryer:
            with attempt:
                res = breaker(_exec)()
                if ctx and ctx.event_writer:
                    ctx.event_writer.write(
                        EventType.TOOL_RESULT,
                        {"tool_name": name, "effect": effect, "status": "success", "recipe": "mcp_safe_tools"},
                    )
                return res

    async def call_tool_async(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        human_confirmed: bool = False,
    ) -> Any:
        """Async twin: Dispatch tool call through MCP with retry, breaker, and ActionGate gating."""
        return await asyncio.to_thread(
            self.call_tool,
            name=name,
            arguments=arguments,
            human_confirmed=human_confirmed,
        )


def mcp_safe_tools(
    registry: Optional[ToolRegistry] = None,
    action_gate: Optional[ActionGate] = None,
    max_attempts: int = 3,
    fail_max: int = 5,
    reset_timeout: int = 60,
) -> McpSafeToolsBridge:
    """Create an McpSafeToolsBridge combining retries, circuit breakers, and ActionGate."""
    return McpSafeToolsBridge(
        registry=registry,
        action_gate=action_gate,
        max_attempts=max_attempts,
        fail_max=fail_max,
        reset_timeout=reset_timeout,
    )


async def mcp_safe_tools_async(
    registry: Optional[ToolRegistry] = None,
    action_gate: Optional[ActionGate] = None,
    max_attempts: int = 3,
    fail_max: int = 5,
    reset_timeout: int = 60,
) -> McpSafeToolsBridge:
    """Async twin: Create an McpSafeToolsBridge combining retries, circuit breakers, and ActionGate."""
    return await asyncio.to_thread(
        mcp_safe_tools,
        registry=registry,
        action_gate=action_gate,
        max_attempts=max_attempts,
        fail_max=fail_max,
        reset_timeout=reset_timeout,
    )
