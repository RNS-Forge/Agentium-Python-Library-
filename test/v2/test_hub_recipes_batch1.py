"""Tests for Agentium Batch 1 Integration Recipes (R01, R03, R05, R06, R08)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import agentium
from agentium.core.events import EventReader, EventType
from agentium.lineage.claims import ClaimStore
from agentium.recipes import (
    cached_tool,
    cached_tool_async,
    drift_report,
    drift_report_async,
    fuzzy_verify,
    fuzzy_verify_async,
    safe_call,
    safe_call_async,
    verified_extract,
    verified_extract_async,
)


# ============================================================================
# R01: safe_call & safe_call_async
# ============================================================================

def test_safe_call_retry_and_success():
    attempts = 0

    @safe_call(max_attempts=3, name="flaky_service")
    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionResetError("Transient network drop")
        return "success_payload"

    with agentium.run() as ctx:
        res = flaky_func()
        assert res == "success_payload"
        assert attempts == 3

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    tool_results = [e for e in events if e.type == EventType.TOOL_RESULT.value]
    assert len(tool_results) >= 1
    print("[PASS] test_safe_call_retry_and_success passed.")


def test_safe_call_circuit_breaker():
    import pybreaker

    fail_counter = 0

    @safe_call(max_attempts=1, fail_max=3, reset_timeout=30, name="broken_service")
    def permanently_broken():
        nonlocal fail_counter
        fail_counter += 1
        raise RuntimeError("Service is dead")

    # Call 1 & 2 fail normally
    try:
        permanently_broken()
    except RuntimeError:
        pass

    try:
        permanently_broken()
    except RuntimeError:
        pass

    # Call 3 should trip the circuit breaker immediately
    try:
        permanently_broken()
        assert False, "Expected CircuitBreakerError"
    except pybreaker.CircuitBreakerError:
        print("[PASS] Circuit breaker tripped as expected.")


def test_safe_call_async_twin():
    attempts = 0

    @safe_call_async(max_attempts=2, name="async_flaky")
    async def async_flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise TimeoutError("Temporary async timeout")
        return {"data": 123}

    async def _run():
        res = await async_flaky()
        assert res == {"data": 123}
        assert attempts == 2

    asyncio.run(_run())
    print("[PASS] test_safe_call_async_twin passed.")


# ============================================================================
# R03: cached_tool & cached_tool_async
# ============================================================================

def test_cached_tool_read_invariant():
    try:
        @cached_tool(effect="write")
        def invalid_tool():
            return 1
        assert False, "Expected ValueError on non-read tool"
    except ValueError as exc:
        assert "only be applied to read" in str(exc)
        print("[PASS] cached_tool rejected non-read effect.")


def test_cached_tool_caching_and_claims():
    call_count = 0

    @cached_tool(maxsize=10, ttl=60, name="db_lookup")
    def get_user_profile(user_id: int):
        nonlocal call_count
        call_count += 1
        return {"user_id": user_id, "role": "admin"}

    with agentium.run() as ctx:
        # First call: cache miss
        r1 = get_user_profile(42)
        assert r1 == {"user_id": 42, "role": "admin"}
        assert call_count == 1

        # Second call: cache hit!
        r2 = get_user_profile(42)
        assert r2 == {"user_id": 42, "role": "admin"}
        assert call_count == 1  # Not called again!

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    hits = [e for e in events if e.type == EventType.TOOL_RESULT.value and e.payload.get("cache_hit")]
    assert len(hits) == 1, f"Expected 1 cache hit event, got {len(hits)}"
    print("[PASS] test_cached_tool_caching_and_claims passed.")


def test_cached_tool_async_twin():
    call_count = 0

    @cached_tool_async(maxsize=10, ttl=60, name="async_lookup")
    async def async_get_data(item_id: str):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)
        return f"item_{item_id}"

    async def _run():
        res1 = await async_get_data("abc")
        res2 = await async_get_data("abc")
        assert res1 == "item_abc"
        assert res2 == "item_abc"
        assert call_count == 1

    asyncio.run(_run())
    print("[PASS] test_cached_tool_async_twin passed.")


# ============================================================================
# R05: verified_extract & verified_extract_async
# ============================================================================

def test_verified_extract_sync():
    store = ClaimStore(run_id="extract_test")
    raw_response = {
        "account": {
            "id": "acc_9921",
            "balance": 15420.50,
            "currency": "USD",
        }
    }

    val, claim = verified_extract(
        data=raw_response,
        query="account.balance",
        statement_template="Account balance is {val}",
        source_id="stripe_api",
        claim_store=store,
        verify=True,
    )

    assert val == 15420.50
    assert claim is not None
    assert claim.status == "verified"
    assert claim.statement == "Account balance is 15420.5"
    assert len(claim.evidence) == 1
    assert claim.evidence[0].source_id == "stripe_api"
    print("[PASS] test_verified_extract_sync passed.")


def test_verified_extract_async_twin():
    async def _run():
        store = ClaimStore(run_id="extract_async_test")
        payload = {"status": "ok", "items": ["a", "b", "c"]}
        val, claim = await verified_extract_async(
            data=payload,
            query="items[1]",
            statement_template="Second item is {val}",
            claim_store=store,
        )
        assert val == "b"
        assert claim.status == "verified"

    asyncio.run(_run())
    print("[PASS] test_verified_extract_async_twin passed.")


# ============================================================================
# R06: fuzzy_verify & fuzzy_verify_async
# ============================================================================

def test_fuzzy_verify_match():
    store = ClaimStore(run_id="fuzzy_test")
    claim_text = "Alice purchased 3 apples for $15."
    source_text = "Transaction summary: Customer Alice purchased 3 apples for $15 on October 4th."

    is_supported, score, claim = fuzzy_verify(
        claim_text=claim_text,
        source_text=source_text,
        threshold=0.85,
        claim_store=store,
    )

    assert is_supported is True
    assert score >= 0.85
    assert claim is not None
    assert claim.status == "verified"
    assert claim.verified_by == "fuzzy_verifier"
    print(f"[PASS] test_fuzzy_verify_match passed with score {score:.3f}.")


def test_fuzzy_verify_mismatch_refute():
    store = ClaimStore(run_id="fuzzy_refute_test")
    claim_text = "Alice purchased a new Tesla car."
    source_text = "Transaction summary: Customer Alice purchased 3 apples for $15."

    is_supported, score, claim = fuzzy_verify(
        claim_text=claim_text,
        source_text=source_text,
        threshold=0.85,
        claim_store=store,
    )

    assert is_supported is False
    assert score < 0.85
    assert claim is not None
    assert claim.status == "refuted"
    print(f"[PASS] test_fuzzy_verify_mismatch_refute passed with refuted score {score:.3f}.")


def test_fuzzy_verify_async_twin():
    async def _run():
        is_supported, score, _ = await fuzzy_verify_async(
            claim_text="Payment approved",
            source_text="Status: Payment approved by gateway.",
            threshold=0.80,
        )
        assert is_supported is True

    asyncio.run(_run())
    print("[PASS] test_fuzzy_verify_async_twin passed.")


# ============================================================================
# R08: drift_report & drift_report_async
# ============================================================================

def test_drift_report_no_drift():
    baseline = {"model": "gpt-4o", "temperature": 0.2, "tools": ["search", "calc"]}
    target = {"model": "gpt-4o", "temperature": 0.2, "tools": ["search", "calc"]}

    report = drift_report(baseline, target, baseline_id="v1", target_id="v2")
    assert report.has_drift is False
    assert report.changes == {}
    assert "No drift detected" in report.summary
    print("[PASS] test_drift_report_no_drift passed.")


def test_drift_report_with_drift():
    baseline = {"model": "gpt-4o", "temperature": 0.2, "tools": ["search"]}
    target = {"model": "gpt-4o", "temperature": 0.7, "tools": ["search", "bash"]}

    report = drift_report(baseline, target, baseline_id="prod", target_id="staging")
    assert report.has_drift is True
    assert len(report.changes) > 0
    assert "Drift detected" in report.summary
    print("[PASS] test_drift_report_with_drift passed.")


def test_drift_report_async_twin():
    async def _run():
        report = await drift_report_async({"a": 1}, {"a": 2})
        assert report.has_drift is True

    asyncio.run(_run())
    print("[PASS] test_drift_report_async_twin passed.")


if __name__ == "__main__":
    print("--- R01 safe_call ---")
    test_safe_call_retry_and_success()
    test_safe_call_circuit_breaker()
    test_safe_call_async_twin()

    print("\n--- R03 cached_tool ---")
    test_cached_tool_read_invariant()
    test_cached_tool_caching_and_claims()
    test_cached_tool_async_twin()

    print("\n--- R05 verified_extract ---")
    test_verified_extract_sync()
    test_verified_extract_async_twin()

    print("\n--- R06 fuzzy_verify ---")
    test_fuzzy_verify_match()
    test_fuzzy_verify_mismatch_refute()
    test_fuzzy_verify_async_twin()

    print("\n--- R08 drift_report ---")
    test_drift_report_no_drift()
    test_drift_report_with_drift()
    test_drift_report_async_twin()

    print("\nALL BATCH 1 RECIPE TESTS PASSED!")
