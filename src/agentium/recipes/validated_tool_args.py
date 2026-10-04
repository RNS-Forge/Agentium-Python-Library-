"""Recipe R23: validated_tool_args (pydantic + jsonschema + @agentium.tool).

Validates tool arguments against a Pydantic model or JSON Schema before invocation,
logging validation errors through Agentium event tracing and preventing invalid calls.
"""
from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run

T = TypeVar("T")


def validated_tool_args(
    fn: Optional[Callable[..., T]] = None,
    *,
    schema: Optional[Union[Type[Any], Dict[str, Any]]] = None,
    name: Optional[str] = None,
    effect: str = "read",
) -> Any:
    """Decorator to enforce strict Pydantic or JSONSchema validation on tool arguments."""
    def decorator(target_fn: Callable[..., T]) -> Callable[..., T]:
        tool_name = name or getattr(target_fn, "__name__", "validated_tool")
        sig = inspect.signature(target_fn)

        @functools.wraps(target_fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Bind arguments to signature to get parameter dictionary
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            call_kwargs = dict(bound.arguments)

            # Validate against schema
            if schema is not None:
                if isinstance(schema, type):
                    # Pydantic model
                    try:
                        from ..adapters import pydantic_adapter
                        pydantic_adapter.validate(schema, call_kwargs)
                    except ImportError as exc:
                        raise ImportError(
                            f"Recipe 'validated_tool_args' with Pydantic requires 'pydantic'. "
                            f"Install via: pip install '{PACKAGE_NAME}[pydantic]'"
                        ) from exc
                    except Exception as err:
                        ctx = get_current_run()
                        if ctx and ctx.event_writer:
                            ctx.event_writer.write(
                                EventType.TOOL_RESULT,
                                {"tool_name": tool_name, "status": "validation_error", "error": str(err)},
                            )
                        raise ValueError(f"Tool '{tool_name}' argument validation failed: {err}") from err
                elif isinstance(schema, dict):
                    # JSON Schema
                    try:
                        from ..adapters import jsonschema_adapter
                        jsonschema_adapter.validate(call_kwargs, schema)
                    except ImportError as exc:
                        raise ImportError(
                            f"Recipe 'validated_tool_args' with JSON schema requires 'jsonschema'. "
                            f"Install via: pip install '{PACKAGE_NAME}[jsonschema]'"
                        ) from exc
                    except Exception as err:
                        ctx = get_current_run()
                        if ctx and ctx.event_writer:
                            ctx.event_writer.write(
                                EventType.TOOL_RESULT,
                                {"tool_name": tool_name, "status": "validation_error", "error": str(err)},
                            )
                        raise ValueError(f"Tool '{tool_name}' argument validation failed: {err}") from err

            # Execute tool
            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "effect": effect, "recipe": "validated_tool_args"},
                )

            res = target_fn(*args, **kwargs)

            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": tool_name, "effect": effect, "status": "success"},
                )
            return res

        wrapper.raw = target_fn  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        wrapper.__name__ = tool_name
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def validated_tool_args_async(
    fn: Optional[Callable[..., Any]] = None,
    *,
    schema: Optional[Union[Type[Any], Dict[str, Any]]] = None,
    name: Optional[str] = None,
    effect: str = "read",
) -> Any:
    """Async decorator to enforce strict Pydantic or JSONSchema validation on tool arguments."""
    def decorator(target_fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or getattr(target_fn, "__name__", "validated_tool_async")
        sig = inspect.signature(target_fn)

        @functools.wraps(target_fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            call_kwargs = dict(bound.arguments)

            if schema is not None:
                if isinstance(schema, type):
                    try:
                        from ..adapters import pydantic_adapter
                        pydantic_adapter.validate(schema, call_kwargs)
                    except ImportError as exc:
                        raise ImportError(
                            f"Recipe 'validated_tool_args' with Pydantic requires 'pydantic'. "
                            f"Install via: pip install '{PACKAGE_NAME}[pydantic]'"
                        ) from exc
                    except Exception as err:
                        ctx = get_current_run()
                        if ctx and ctx.event_writer:
                            ctx.event_writer.write(
                                EventType.TOOL_RESULT,
                                {"tool_name": tool_name, "status": "validation_error", "error": str(err)},
                            )
                        raise ValueError(f"Tool '{tool_name}' argument validation failed: {err}") from err
                elif isinstance(schema, dict):
                    try:
                        from ..adapters import jsonschema_adapter
                        jsonschema_adapter.validate(call_kwargs, schema)
                    except ImportError as exc:
                        raise ImportError(
                            f"Recipe 'validated_tool_args' with JSON schema requires 'jsonschema'. "
                            f"Install via: pip install '{PACKAGE_NAME}[jsonschema]'"
                        ) from exc
                    except Exception as err:
                        ctx = get_current_run()
                        if ctx and ctx.event_writer:
                            ctx.event_writer.write(
                                EventType.TOOL_RESULT,
                                {"tool_name": tool_name, "status": "validation_error", "error": str(err)},
                            )
                        raise ValueError(f"Tool '{tool_name}' argument validation failed: {err}") from err

            ctx = get_current_run()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "effect": effect, "async": True, "recipe": "validated_tool_args"},
                )

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

        wrapper.raw = target_fn  # type: ignore
        wrapper.__agentium_tool_effect__ = effect  # type: ignore
        wrapper.__name__ = tool_name
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator
