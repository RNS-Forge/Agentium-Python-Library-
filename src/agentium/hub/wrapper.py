"""Universal object and callable wrapper for Agentium v2 (M5b).

Integrates external library callables into Agentium's event tracing,
effect tagging (for ActionGate F4 and Speculative Prefetch F10), and
lineage without altering return values, mutating exceptions, or modifying
underlying library behavior. Exposes `.raw` to access the original object.
"""
from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union

from ..core.events import EventType, EventWriter
from ..core.run import get_current_run

T = TypeVar("T")
VALID_EFFECTS = {"read", "write", "destructive"}


class WrappedCallable(Generic[T]):
    """Wrapper around a sync callable adding event emission and effect metadata."""

    def __init__(
        self,
        fn: Callable[..., T],
        name: Optional[str] = None,
        effect: str = "read",
        event_writer: Optional[EventWriter] = None,
    ) -> None:
        self._raw = fn
        self.__name__ = name or getattr(fn, "__name__", "wrapped_callable")
        self.__doc__ = getattr(fn, "__doc__", None)
        self.effect = effect.lower()
        if self.effect not in VALID_EFFECTS:
            raise ValueError(f"Invalid effect '{effect}'. Must be one of {sorted(VALID_EFFECTS)}")
        self.event_writer = event_writer
        self.__agentium_tool_effect__ = self.effect

    @property
    def raw(self) -> Callable[..., T]:
        """Direct access to the underlying unwrapped callable."""
        return self._raw

    def _get_writer(self) -> Optional[EventWriter]:
        if self.event_writer is not None:
            return self.event_writer
        ctx = get_current_run()
        return ctx.event_writer if ctx is not None else None

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        writer = self._get_writer()
        if writer:
            writer.write(
                EventType.TOOL_CALL,
                {"tool_name": self.__name__, "effect": self.effect, "args_count": len(args)},
            )

        try:
            result = self._raw(*args, **kwargs)
            if writer:
                writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": self.__name__, "effect": self.effect, "status": "success"},
                )
            return result
        except BaseException as exc:
            if writer:
                writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": self.__name__, "effect": self.effect, "status": "error", "error": type(exc).__name__},
                )
            raise


class WrappedAsyncCallable(Generic[T]):
    """Wrapper around an async callable/coroutine adding event emission and effect metadata."""

    def __init__(
        self,
        fn: Callable[..., Any],
        name: Optional[str] = None,
        effect: str = "read",
        event_writer: Optional[EventWriter] = None,
    ) -> None:
        self._raw = fn
        self.__name__ = name or getattr(fn, "__name__", "wrapped_async_callable")
        self.__doc__ = getattr(fn, "__doc__", None)
        self.effect = effect.lower()
        if self.effect not in VALID_EFFECTS:
            raise ValueError(f"Invalid effect '{effect}'. Must be one of {sorted(VALID_EFFECTS)}")
        self.event_writer = event_writer
        self.__agentium_tool_effect__ = self.effect

    @property
    def raw(self) -> Callable[..., Any]:
        """Direct access to the underlying unwrapped async callable."""
        return self._raw

    def _get_writer(self) -> Optional[EventWriter]:
        if self.event_writer is not None:
            return self.event_writer
        ctx = get_current_run()
        return ctx.event_writer if ctx is not None else None

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        writer = self._get_writer()
        if writer:
            writer.write(
                EventType.TOOL_CALL,
                {"tool_name": self.__name__, "effect": self.effect, "args_count": len(args), "async": True},
            )

        try:
            result = await self._raw(*args, **kwargs)
            if writer:
                writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": self.__name__, "effect": self.effect, "status": "success", "async": True},
                )
            return result
        except BaseException as exc:
            if writer:
                writer.write(
                    EventType.TOOL_RESULT,
                    {"tool_name": self.__name__, "effect": self.effect, "status": "error", "error": type(exc).__name__, "async": True},
                )
            raise


class ObjectWrapper:
    """Wrapper around any Python object/client exposing methods with .raw access."""

    def __init__(
        self,
        obj: Any,
        name: Optional[str] = None,
        effect: str = "read",
        event_writer: Optional[EventWriter] = None,
    ) -> None:
        self._raw = obj
        self._name = name or type(obj).__name__
        self._effect = effect
        self._event_writer = event_writer

    @property
    def raw(self) -> Any:
        return self._raw

    def __getattr__(self, item: str) -> Any:
        attr = getattr(self._raw, item)
        if callable(attr):
            method_name = f"{self._name}.{item}"
            if asyncio.iscoroutinefunction(attr):
                return WrappedAsyncCallable(attr, name=method_name, effect=self._effect, event_writer=self._event_writer)
            return WrappedCallable(attr, name=method_name, effect=self._effect, event_writer=self._event_writer)
        return attr


def wrap(
    obj: Any,
    name: Optional[str] = None,
    effect: str = "read",
    event_writer: Optional[EventWriter] = None,
) -> Any:
    """Universal wrapper for any callable or object from any library.

    - Emits Agentium events.
    - Applies effect tag (enabling ActionGate F4 and Speculative Prefetch F10).
    - Preserves exact return values and exceptions.
    - Exposes `.raw` to access the underlying unwrapped object.
    """
    if asyncio.iscoroutinefunction(obj):
        return WrappedAsyncCallable(obj, name=name, effect=effect, event_writer=event_writer)
    elif callable(obj):
        return WrappedCallable(obj, name=name, effect=effect, event_writer=event_writer)
    return ObjectWrapper(obj, name=name, effect=effect, event_writer=event_writer)


def wrap_async(
    obj: Any,
    name: Optional[str] = None,
    effect: str = "read",
    event_writer: Optional[EventWriter] = None,
) -> Any:
    """Explicit async universal wrapper for coroutine functions and async objects."""
    if callable(obj) and not asyncio.iscoroutinefunction(obj):
        # Convert sync callable to run in thread executor if wrapped with wrap_async
        @functools.wraps(obj)
        async def async_twin(*args: Any, **kwargs: Any) -> Any:
            return await asyncio.to_thread(obj, *args, **kwargs)
        return WrappedAsyncCallable(async_twin, name=name, effect=effect, event_writer=event_writer)
    elif callable(obj):
        return WrappedAsyncCallable(obj, name=name, effect=effect, event_writer=event_writer)
    return ObjectWrapper(obj, name=name, effect=effect, event_writer=event_writer)
