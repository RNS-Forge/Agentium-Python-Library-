"""Recipe R27: llm_failover (litellm + tenacity + pybreaker).

Multi-provider LLM failover routing with a dedicated circuit breaker per model/provider,
automatically routing traffic away from failing or degraded providers.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Union

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run

# Global registry of circuit breakers per provider name
_BREAKER_POOL: Dict[str, Any] = {}


def _get_breaker_for_provider(provider_name: str, fail_max: int = 3, reset_timeout: int = 60) -> Any:
    import pybreaker
    if provider_name not in _BREAKER_POOL:
        _BREAKER_POOL[provider_name] = pybreaker.CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            name=f"breaker_{provider_name}",
        )
    return _BREAKER_POOL[provider_name]


def llm_failover(
    prompt: Union[str, List[Dict[str, str]]],
    models: List[str],
    fail_max: int = 3,
    reset_timeout: int = 60,
    llm_callable: Optional[Callable[[str, str], str]] = None,
    **kwargs: Any,
) -> str:
    """Execute LLM call across ordered models with individual circuit breakers per provider.

    Args:
        prompt: User prompt or message history.
        models: Ordered list of models to try in sequence (e.g. ['gpt-4o', 'claude-3-5-sonnet', 'gemini-1.5-pro']).
        fail_max: Failures threshold before a provider's circuit breaker opens.
        reset_timeout: Seconds before an open breaker transitions to half-open.
        llm_callable: Optional custom callable (model_name, prompt_str) -> response_str.
        **kwargs: Extra parameters passed to the model invocation.

    Returns:
        Generated text response string from the first successful provider.
    """
    try:
        import pybreaker
    except ImportError as exc:
        raise ImportError(
            f"Recipe 'llm_failover' requires 'pybreaker'. "
            f"Install via: pip install '{PACKAGE_NAME}[pybreaker]'"
        ) from exc

    if not models:
        raise ValueError("At least one model must be provided in 'models' list.")

    prompt_str = prompt if isinstance(prompt, str) else " ".join(m.get("content", "") for m in prompt)
    last_error: Optional[Exception] = None

    ctx = get_current_run()

    for idx, model_name in enumerate(models):
        breaker = _get_breaker_for_provider(model_name, fail_max=fail_max, reset_timeout=reset_timeout)

        # Check if circuit is already open; skip immediately to avoid latency
        if breaker.current_state == "open":
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.LLM_CALL,
                    {
                        "recipe": "llm_failover",
                        "model": model_name,
                        "status": "circuit_open_skipped",
                        "index": idx,
                    },
                )
            continue

        def _do_call() -> str:
            if llm_callable is not None:
                return llm_callable(model_name, prompt_str)
            try:
                from ..adapters import litellm_adapter
                messages = [{"role": "user", "content": prompt_str}] if isinstance(prompt, str) else prompt
                resp = litellm_adapter.completion(model=model_name, messages=messages, **kwargs)
                return resp.choices[0].message.content
            except ImportError as exc:
                raise ImportError(
                    f"Calling default provider requires 'litellm'. "
                    f"Install via: pip install '{PACKAGE_NAME}[litellm]' or supply llm_callable."
                ) from exc

        try:
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.LLM_CALL,
                    {"recipe": "llm_failover", "model": model_name, "status": "attempting", "index": idx},
                )
            # Call through provider's circuit breaker
            res = breaker(_do_call)()
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.LLM_CALL,
                    {"recipe": "llm_failover", "model": model_name, "status": "success"},
                )
            return res
        except (Exception, pybreaker.CircuitBreakerError) as exc:
            last_error = exc
            if ctx and ctx.event_writer:
                ctx.event_writer.write(
                    EventType.LLM_CALL,
                    {
                        "recipe": "llm_failover",
                        "model": model_name,
                        "status": "failed",
                        "error": str(exc),
                        "failing_over": idx < len(models) - 1,
                    },
                )
            continue

    raise RuntimeError(f"All providers in failover chain failed. Last error: {last_error}")


async def llm_failover_async(
    prompt: Union[str, List[Dict[str, str]]],
    models: List[str],
    fail_max: int = 3,
    reset_timeout: int = 60,
    async_llm_callable: Optional[Callable[[str, str], Any]] = None,
    **kwargs: Any,
) -> str:
    """Async twin: Execute LLM call across ordered models with individual circuit breakers."""
    if async_llm_callable is not None:
        last_err = None
        for model_name in models:
            breaker = _get_breaker_for_provider(model_name, fail_max=fail_max, reset_timeout=reset_timeout)
            if breaker.current_state == "open":
                continue
            try:
                # Wrap async call with breaker state handling
                res = await async_llm_callable(model_name, prompt if isinstance(prompt, str) else str(prompt))
                breaker.state.on_success()
                return res
            except Exception as exc:
                breaker.state.on_failure(exc)
                last_err = exc
                continue
        raise RuntimeError(f"All providers in failover chain failed: {last_err}")

    return await asyncio.to_thread(
        llm_failover,
        prompt=prompt,
        models=models,
        fail_max=fail_max,
        reset_timeout=reset_timeout,
        **kwargs,
    )
