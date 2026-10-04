"""Recipe R02: structured_llm (litellm + jsonrepair + pydantic + tenacity).

Calls any model, automatically repairs malformed/truncated LLM JSON,
validates the output against a Pydantic model, and retries failures with backoff.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run

T = TypeVar("T")


def structured_llm(
    prompt: Union[str, List[Dict[str, str]]],
    model_cls: Type[T],
    model: str = "gpt-4o-mini",
    llm_callable: Optional[Callable[[Any], str]] = None,
    max_attempts: int = 3,
    **kwargs: Any,
) -> T:
    """Execute LLM call, repair JSON, validate against Pydantic model, and retry on failure.

    Args:
        prompt: User prompt string or list of message dictionaries.
        model_cls: Pydantic model class to validate and parse output into.
        model: Model identifier for LiteLLM.
        llm_callable: Optional custom callable to invoke instead of LiteLLM.
        max_attempts: Maximum retry attempts with tenacity.
        **kwargs: Extra parameters passed to the model invocation.

    Returns:
        Validated Pydantic model instance of type T.
    """
    try:
        import tenacity
        from ..adapters import jsonrepair_adapter, pydantic_adapter
    except ImportError as exc:
        raise ImportError(
            f"Recipe 'structured_llm' requires 'tenacity', 'jsonrepair', and 'pydantic'. "
            f"Install via: pip install '{PACKAGE_NAME}[tenacity,jsonrepair,pydantic]'"
        ) from exc

    retryer = tenacity.Retrying(
        stop=tenacity.stop_after_attempt(max_attempts),
        wait=tenacity.wait_exponential(multiplier=0.1, min=0.1, max=1.0),
        reraise=True,
    )

    def _execute_single_attempt() -> T:
        ctx = get_current_run()
        if ctx and ctx.event_writer:
            ctx.event_writer.write(
                EventType.LLM_CALL,
                {"recipe": "structured_llm", "model": model, "target_schema": model_cls.__name__},
            )

        if llm_callable is not None:
            raw_response = llm_callable(prompt)
        else:
            try:
                from ..adapters import litellm_adapter
                messages = [{"role": "user", "content": prompt}] if isinstance(prompt, str) else prompt
                resp = litellm_adapter.completion(model=model, messages=messages, **kwargs)
                raw_response = resp.choices[0].message.content
            except ImportError as exc:
                raise ImportError(
                    f"Calling default provider requires 'litellm'. "
                    f"Install via: pip install '{PACKAGE_NAME}[litellm]' or supply llm_callable."
                ) from exc

        # Repair and parse JSON
        parsed_dict = jsonrepair_adapter.loads(str(raw_response))
        # Validate into target Pydantic model
        validated = pydantic_adapter.validate(model_cls, parsed_dict)
        return validated

    for attempt in retryer:
        with attempt:
            return _execute_single_attempt()

    raise RuntimeError("Structured LLM call failed after retries.")


async def structured_llm_async(
    prompt: Union[str, List[Dict[str, str]]],
    model_cls: Type[T],
    model: str = "gpt-4o-mini",
    async_llm_callable: Optional[Callable[[Any], Any]] = None,
    max_attempts: int = 3,
    **kwargs: Any,
) -> T:
    """Async twin: Execute LLM call, repair JSON, validate against Pydantic model, and retry on failure."""
    if async_llm_callable is not None:
        try:
            import tenacity
            from ..adapters import jsonrepair_adapter, pydantic_adapter
        except ImportError as exc:
            raise ImportError(
                f"Recipe 'structured_llm' requires 'tenacity', 'jsonrepair', and 'pydantic'. "
                f"Install via: pip install '{PACKAGE_NAME}[tenacity,jsonrepair,pydantic]'"
            ) from exc

        # Use loop or to_thread for retry
        raw_res = await async_llm_callable(prompt)
        parsed = jsonrepair_adapter.loads(str(raw_res))
        return pydantic_adapter.validate(model_cls, parsed)

    return await asyncio.to_thread(
        structured_llm,
        prompt=prompt,
        model_cls=model_cls,
        model=model,
        max_attempts=max_attempts,
        **kwargs,
    )
