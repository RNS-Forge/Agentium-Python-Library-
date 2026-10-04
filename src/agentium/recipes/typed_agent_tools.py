"""Recipe R44: typed_agent_tools (openai-agents / openai + pydantic).

Creates typed, schema-validated agent tools compatible with OpenAI Agents SDK
and Function Calling protocols, carrying Agentium effect tags ('read', 'write', 'destructive').
"""
from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run

T = TypeVar("T")


def typed_agent_tools(
    fn: Optional[Callable[..., T]] = None,
    *,
    schema: Optional[Type[Any]] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    effect: str = "read",
) -> Any:
    """Decorator to produce a typed agent tool with OpenAI schema definition and Agentium effect tagging."""
    def decorator(target_fn: Callable[..., T]) -> Callable[..., T]:
        tool_name = name or getattr(target_fn, "__name__", "agent_tool")
        doc = description or inspect.getdoc(target_fn) or ""

        # Extract JSON Schema if Pydantic model provided
        param_schema: Dict[str, Any] = {"type": "object", "properties": {}}
        if schema is not None:
            try:
                from ..adapters import pydantic_adapter
                param_schema = pydantic_adapter.to_schema(schema)
            except ImportError as exc:
                raise ImportError(
                    f"Recipe 'typed_agent_tools' with Pydantic schema requires 'pydantic'. "
                    f"Install via: pip install '{PACKAGE_NAME}[pydantic]'"
                ) from exc

        # Format standard OpenAI function descriptor
        openai_definition = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": doc.strip(),
                "parameters": param_schema,
            },
        }

        @functools.wraps(target_fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "effect": effect, "recipe": "typed_agent_tools"},
                )

            # Validate kwargs against schema if present
            if schema is not None and kwargs:
                try:
                    from ..adapters import pydantic_adapter
                    pydantic_adapter.validate(schema, kwargs)
                except Exception as err:
                    if ctx and ctx.event_writer:
                        ctx.event_writer.write(
                            EventType.TOOL_RESULT,
                            {"tool_name": tool_name, "status": "validation_error", "error": str(err)},
                        )
                    raise ValueError(f"Agent tool '{tool_name}' argument validation failed: {err}") from err

            res = target_fn(*args, **kwargs)

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": tool_name, "effect": effect, "status": "success"},
                )
            return res

        wrapper.raw = target_fn  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        wrapper.openai_schema = openai_definition  # type: ignore
        wrapper.parameters_schema = param_schema  # type: ignore
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def typed_agent_tools_async(
    fn: Optional[Callable[..., Any]] = None,
    *,
    schema: Optional[Type[Any]] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    effect: str = "read",
) -> Any:
    """Async twin: Decorator to produce a typed agent tool with OpenAI schema and effect tagging."""
    def decorator(target_fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or getattr(target_fn, "__name__", "async_agent_tool")
        doc = description or inspect.getdoc(target_fn) or ""

        param_schema: Dict[str, Any] = {"type": "object", "properties": {}}
        if schema is not None:
            from ..adapters import pydantic_adapter
            param_schema = pydantic_adapter.to_schema(schema)

        openai_definition = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": doc.strip(),
                "parameters": param_schema,
            },
        }

        @functools.wraps(target_fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "effect": effect, "async": True, "recipe": "typed_agent_tools"},
                )

            if schema is not None and kwargs:
                from ..adapters import pydantic_adapter
                pydantic_adapter.validate(schema, kwargs)

            if asyncio.iscoroutinefunction(target_fn):
                res = await target_fn(*args, **kwargs)
            else:
                res = await asyncio.to_thread(target_fn, *args, **kwargs)

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": tool_name, "effect": effect, "status": "success", "async": True},
                )
            return res

        async_wrapper.raw = target_fn  # type: ignore
        async_wrapper.__agentium_tool_effect__ = effect  # type: ignore
        async_wrapper.openai_schema = openai_definition  # type: ignore
        async_wrapper.parameters_schema = param_schema  # type: ignore
        return async_wrapper

    if fn is not None:
        return decorator(fn)
    return decorator
