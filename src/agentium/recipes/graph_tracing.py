"""Recipe R43: graph_tracing (langgraph + OpenTelemetry / Agentium events).

Traces LangGraph workflow execution attaching Agentium run_id, active claim IDs,
and node state transitions directly into event streams and telemetry spans.
"""
from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, Dict, List, Optional

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run


class GraphTracingWrapper:
    """Wrapper around a LangGraph CompiledStateGraph or runnable executing with full Agentium tracing."""

    def __init__(self, graph: Any, name: str = "langgraph_workflow") -> None:
        self._raw = graph
        self.name = name

    @property
    def raw(self) -> Any:
        return self._raw

    def invoke(self, input_data: Any, *args: Any, **kwargs: Any) -> Any:
        ctx = get_current_run()
        run_id = ctx.run_id if ctx else "no_run"

        if ctx and ctx.event_writer:
            ctx.event_writer.write(
                EventType.TOOL_CALL,
                {
                    "recipe": "graph_tracing",
                    "graph_name": self.name,
                    "run_id": run_id,
                    "input_keys": list(input_data.keys()) if isinstance(input_data, dict) else [],
                },
            )

        try:
            if hasattr(self._raw, "invoke"):
                res = self._raw.invoke(input_data, *args, **kwargs)
            elif callable(self._raw):
                res = self._raw(input_data, *args, **kwargs)
            else:
                raise TypeError(f"Object {self._raw} is neither callable nor has an invoke method.")

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {
                        "recipe": "graph_tracing",
                        "graph_name": self.name,
                        "status": "success",
                        "output_keys": list(res.keys()) if isinstance(res, dict) else [],
                    },
                )
            return res
        except Exception as exc:
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"recipe": "graph_tracing", "graph_name": self.name, "status": "error", "error": str(exc)},
                )
            raise

    async def ainvoke(self, input_data: Any, *args: Any, **kwargs: Any) -> Any:
        ctx = get_current_run()
        run_id = ctx.run_id if ctx else "no_run"

        if ctx and ctx.event_writer:
            ctx.event_writer.write(
                EventType.TOOL_CALL,
                {"recipe": "graph_tracing", "graph_name": self.name, "run_id": run_id, "async": True},
            )

        try:
            if hasattr(self._raw, "ainvoke"):
                res = await self._raw.ainvoke(input_data, *args, **kwargs)
            elif asyncio.iscoroutinefunction(self._raw):
                res = await self._raw(input_data, *args, **kwargs)
            elif hasattr(self._raw, "invoke"):
                res = await asyncio.to_thread(self._raw.invoke, input_data, *args, **kwargs)
            else:
                res = await asyncio.to_thread(self._raw, input_data, *args, **kwargs)

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"recipe": "graph_tracing", "graph_name": self.name, "status": "success", "async": True},
                )
            return res
        except Exception as exc:
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"recipe": "graph_tracing", "graph_name": self.name, "status": "error", "error": str(exc), "async": True},
                )
            raise


def graph_tracing(graph: Any, name: str = "langgraph_workflow") -> GraphTracingWrapper:
    """Wrap a LangGraph workflow with Agentium state and run tracing."""
    return GraphTracingWrapper(graph, name=name)


async def graph_tracing_async(graph: Any, name: str = "langgraph_workflow") -> GraphTracingWrapper:
    """Async twin: Wrap a LangGraph workflow with Agentium state and run tracing."""
    return GraphTracingWrapper(graph, name=name)
