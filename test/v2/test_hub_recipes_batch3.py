"""Tests for Agentium Batch 3 Integration Recipes (R22, R27, R28, R39)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import agentium
from agentium.core.events import EventReader, EventType
from agentium.recipes import (
    BudgetExceededError,
    api_call_safe,
    api_call_safe_async,
    budget_llm,
    budget_llm_async,
    llm_failover,
    llm_failover_async,
    traced_retry,
    traced_retry_async,
)


# ============================================================================
# R22: budget_llm & budget_llm_async
# ============================================================================

def test_budget_llm_routing_and_budget_cap():
    call_log = []

    def mock_llm(model: str, prompt: str) -> str:
        call_log.append(model)
        return f"Response from {model}"

    # 1. Under budget call -> uses primary model "gpt-4o"
    with agentium.run() as ctx:
        res = budget_llm(
            prompt="Hello short prompt",
            model="gpt-4o",
            fallback_model="gpt-4o-mini",
            max_tokens_budget=100,
            llm_callable=mock_llm,
        )
        assert res == "Response from gpt-4o"
        assert call_log[-1] == "gpt-4o"

    # 2. Over budget call -> routes to fallback model "gpt-4o-mini"
    huge_prompt = "word " * 500  # ~500 tokens
    with agentium.run() as ctx:
        res = budget_llm(
            prompt=huge_prompt,
            model="gpt-4o",
            fallback_model="gpt-4o-mini",
            max_tokens_budget=100,
            llm_callable=mock_llm,
        )
        assert res == "Response from gpt-4o-mini"
        assert call_log[-1] == "gpt-4o-mini"

    # 3. Over budget call without fallback -> raises BudgetExceededError
    try:
        budget_llm(
            prompt=huge_prompt,
            model="gpt-4o",
            fallback_model=None,
            max_tokens_budget=100,
            llm_callable=mock_llm,
        )
        assert False, "Expected BudgetExceededError"
    except BudgetExceededError:
        print("[PASS] BudgetExceededError raised when no fallback model available.")

    print("[PASS] test_budget_llm_routing_and_budget_cap passed.")


def test_budget_llm_async_twin():
    async def mock_async_llm(model: str, prompt: str) -> str:
        await asyncio.sleep(0.01)
        return f"Async response from {model}"

    async def _run():
        res = await budget_llm_async(
            prompt="Simple query",
            model="claude-3-5-sonnet",
            fallback_model="claude-3-5-haiku",
            max_tokens_budget=200,
            async_llm_callable=mock_async_llm,
        )
        assert res == "Async response from claude-3-5-sonnet"

    asyncio.run(_run())
    print("[PASS] test_budget_llm_async_twin passed.")


# ============================================================================
# R27: llm_failover & llm_failover_async
# ============================================================================

def test_llm_failover_provider_fallback():
    attempts = []

    def mock_flaky_llm(model: str, prompt: str) -> str:
        attempts.append(model)
        if model == "provider_a":
            raise ConnectionError("Provider A is down with 502 Bad Gateway")
        return f"Success from {model}"

    with agentium.run() as ctx:
        res = llm_failover(
            prompt="Analyze system logs",
            models=["provider_a", "provider_b", "provider_c"],
            fail_max=2,
            llm_callable=mock_flaky_llm,
        )

        assert res == "Success from provider_b"
        assert attempts == ["provider_a", "provider_b"]

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    llm_events = [e for e in events if e.type == EventType.LLM_CALL.value]
    assert len(llm_events) >= 2
    print("[PASS] test_llm_failover_provider_fallback passed.")


def test_llm_failover_async_twin():
    async def mock_async_flaky(model: str, prompt: str) -> str:
        await asyncio.sleep(0.01)
        if model == "bad_model":
            raise RuntimeError("Out of capacity")
        return f"Async success from {model}"

    async def _run():
        res = await llm_failover_async(
            prompt="Hello",
            models=["bad_model", "good_model"],
            async_llm_callable=mock_async_flaky,
        )
        assert res == "Async success from good_model"

    asyncio.run(_run())
    print("[PASS] test_llm_failover_async_twin passed.")


# ============================================================================
# R28: api_call_safe & api_call_safe_async
# ============================================================================

def test_api_call_safe_read_invariants():
    # 1. Reject non-read effect
    try:
        api_call_safe("https://api.example.com", effect="write")
        assert False, "Expected ValueError on effect='write'"
    except ValueError as exc:
        assert "only be applied to read operations" in str(exc)

    # 2. Reject non-read method
    try:
        api_call_safe("https://api.example.com", method="POST", effect="read")
        assert False, "Expected ValueError on POST method"
    except ValueError as exc:
        assert "requires a read-only HTTP method" in str(exc)

    print("[PASS] test_api_call_safe_read_invariants passed.")


def test_api_call_safe_retry_and_success():
    calls = 0

    class MockHttpClient:
        def request(self, method, url, **kwargs):
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ConnectionResetError("Remote server closed connection")
            return {"status": 200, "data": "payload_ok"}

    client = MockHttpClient()

    with agentium.run() as ctx:
        res = api_call_safe(
            url="https://api.example.com/v1/metrics",
            method="GET",
            max_attempts=3,
            client=client,
            name="fetch_metrics",
        )
        assert res == {"status": 200, "data": "payload_ok"}
        assert calls == 3

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    tool_calls = [e for e in events if e.type == EventType.TOOL_CALL.value]
    tool_results = [e for e in events if e.type == EventType.TOOL_RESULT.value]
    assert len(tool_calls) == 1
    assert len(tool_results) == 1
    assert tool_results[0].payload["status"] == "success"
    print("[PASS] test_api_call_safe_retry_and_success passed.")


def test_api_call_safe_async_twin():
    class MockHttpClient:
        def request(self, method, url, **kwargs):
            return {"status": 200, "async": True}

    async def _run():
        res = await api_call_safe_async(
            url="https://api.example.com/status",
            client=MockHttpClient(),
        )
        assert res == {"status": 200, "async": True}

    asyncio.run(_run())
    print("[PASS] test_api_call_safe_async_twin passed.")


# ============================================================================
# R39: traced_retry & traced_retry_async
# ============================================================================

def test_traced_retry_sync():
    attempts = 0

    @traced_retry(max_attempts=3, wait_min=0.01, wait_max=0.05, name="unstable_db")
    def unstable_query(query: str):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError("DB query timed out")
        return f"Data for {query}"

    with agentium.run() as ctx:
        res = unstable_query("SELECT * FROM users")
        assert res == "Data for SELECT * FROM users"
        assert attempts == 3

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    tool_calls = [e for e in events if e.type == EventType.TOOL_CALL.value and e.payload.get("recipe") == "traced_retry"]
    tool_results = [e for e in events if e.type == EventType.TOOL_RESULT.value and e.payload.get("recipe") == "traced_retry"]

    assert len(tool_calls) == 3, f"Expected 3 tool_call attempts, got {len(tool_calls)}"
    assert len(tool_results) == 3, f"Expected 3 tool_result events, got {len(tool_results)}"
    # First 2 attempts failed, 3rd succeeded
    assert tool_results[0].payload["status"] == "attempt_failed"
    assert tool_results[1].payload["status"] == "attempt_failed"
    assert tool_results[2].payload["status"] == "success"
    print("[PASS] test_traced_retry_sync passed.")


def test_traced_retry_async_twin():
    attempts = 0

    @traced_retry_async(max_attempts=2, wait_min=0.01, wait_max=0.05, name="async_io")
    async def async_io():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("Async network glitch")
        return "async_data"

    async def _run():
        res = await async_io()
        assert res == "async_data"
        assert attempts == 2

    asyncio.run(_run())
    print("[PASS] test_traced_retry_async_twin passed.")


if __name__ == "__main__":
    print("--- R22 budget_llm ---")
    test_budget_llm_routing_and_budget_cap()
    test_budget_llm_async_twin()

    print("\n--- R27 llm_failover ---")
    test_llm_failover_provider_fallback()
    test_llm_failover_async_twin()

    print("\n--- R28 api_call_safe ---")
    test_api_call_safe_read_invariants()
    test_api_call_safe_retry_and_success()
    test_api_call_safe_async_twin()

    print("\n--- R39 traced_retry ---")
    test_traced_retry_sync()
    test_traced_retry_async_twin()

    print("\nALL BATCH 3 RECIPE TESTS PASSED!")
