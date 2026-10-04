"""Recipe R22: budget_llm (litellm + tenacity + token budgeting).

Executes model calls with a strict token/cost budget, retries transient failures with tenacity,
and automatically routes to a lighter fallback model when the budget is constrained.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Union

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run
from ..core.tokens import estimate_tokens


class BudgetExceededError(RuntimeError):
    """Raised when an LLM call exceeds the allocated token or cost budget."""


def budget_llm(
    prompt: Union[str, List[Dict[str, str]]],
    model: str = "gpt-4o",
    fallback_model: Optional[str] = "gpt-4o-mini",
    max_tokens_budget: int = 4000,
    max_attempts: int = 3,
    llm_callable: Optional[Callable[[str, str], str]] = None,
    **kwargs: Any,
) -> str:
    """Execute LLM call enforcing a token budget and fallback model routing.

    Args:
        prompt: User prompt string or list of messages.
        model: Primary model identifier.
        fallback_model: Secondary model identifier if budget constrained or primary fails.
        max_tokens_budget: Maximum allowed estimated input tokens.
        max_attempts: Max retry attempts with tenacity.
        llm_callable: Optional custom callable (model_name, prompt_str) -> response_str.
        **kwargs: Additional parameters forwarded to the model.

    Returns:
        Generated text response string.
    """
    try:
        import tenacity
    except ImportError as exc:
        raise ImportError(
            f"Recipe 'budget_llm' requires 'tenacity'. "
            f"Install via: pip install '{PACKAGE_NAME}[tenacity]'"
        ) from exc

    prompt_str = prompt if isinstance(prompt, str) else " ".join(m.get("content", "") for m in prompt)
    estimated_tokens = estimate_tokens(prompt_str)

    target_model = model
    used_fallback = False

    # Check budget
    if estimated_tokens > max_tokens_budget:
        if fallback_model:
            target_model = fallback_model
            used_fallback = True
        else:
            raise BudgetExceededError(
                f"Prompt token count ({estimated_tokens}) exceeds maximum budget ({max_tokens_budget}) "
                f"and no fallback model was specified."
            )

    retryer = tenacity.Retrying(
        stop=tenacity.stop_after_attempt(max_attempts),
        wait=tenacity.wait_exponential(multiplier=0.1, min=0.1, max=1.0),
        reraise=True,
    )

    ctx = get_current_run()
    if ctx and ctx.event_writer:
        ctx.event_writer.write(
            EventType.LLM_CALL,
            {
                "recipe": "budget_llm",
                "model": target_model,
                "used_fallback": used_fallback,
                "estimated_tokens": estimated_tokens,
                "max_tokens_budget": max_tokens_budget,
            },
        )

    def _call(chosen_model: str) -> str:
        if llm_callable is not None:
            return llm_callable(chosen_model, prompt_str)
        try:
            from ..adapters import litellm_adapter
            messages = [{"role": "user", "content": prompt_str}] if isinstance(prompt, str) else prompt
            resp = litellm_adapter.completion(model=chosen_model, messages=messages, **kwargs)
            return resp.choices[0].message.content
        except ImportError as exc:
            raise ImportError(
                f"Calling default LLM provider requires 'litellm'. "
                f"Install via: pip install '{PACKAGE_NAME}[litellm]' or supply llm_callable."
            ) from exc

    # Attempt with primary/chosen target_model, falling back if primary fails
    try:
        for attempt in retryer:
            with attempt:
                return _call(target_model)
    except Exception as exc:
        if not used_fallback and fallback_model:
            # Fall back to secondary model
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.LLM_CALL,
                    {
                        "recipe": "budget_llm",
                        "model": fallback_model,
                        "used_fallback": True,
                        "reason": f"Primary model {model} failed: {exc}",
                    },
                )
            for attempt in retryer:
                with attempt:
                    return _call(fallback_model)
        raise

    raise RuntimeError("budget_llm failed to produce a response.")


async def budget_llm_async(
    prompt: Union[str, List[Dict[str, str]]],
    model: str = "gpt-4o",
    fallback_model: Optional[str] = "gpt-4o-mini",
    max_tokens_budget: int = 4000,
    max_attempts: int = 3,
    async_llm_callable: Optional[Callable[[str, str], Any]] = None,
    **kwargs: Any,
) -> str:
    """Async twin: Execute LLM call enforcing a token budget and fallback model routing."""
    if async_llm_callable is not None:
        prompt_str = prompt if isinstance(prompt, str) else " ".join(m.get("content", "") for m in prompt)
        estimated_tokens = estimate_tokens(prompt_str)
        target_model = model
        if estimated_tokens > max_tokens_budget:
            if fallback_model:
                target_model = fallback_model
            else:
                raise BudgetExceededError(f"Prompt tokens ({estimated_tokens}) exceed budget ({max_tokens_budget}).")
        return await async_llm_callable(target_model, prompt_str)

    return await asyncio.to_thread(
        budget_llm,
        prompt=prompt,
        model=model,
        fallback_model=fallback_model,
        max_tokens_budget=max_tokens_budget,
        max_attempts=max_attempts,
        **kwargs,
    )
