"""Tests for Agentium Remaining Tier 1 Recipes (R42, R43, R44, R45, R51, R58)."""
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
from agentium.adapters.plain import ToolRegistry, tool
from agentium.core.events import EventReader, EventType
from agentium.lineage.gate import ActionBlockedError, ActionGate
from agentium.recipes import (
    fuzzy_dedupe_cache,
    fuzzy_dedupe_cache_async,
    graph_retry,
    graph_retry_async,
    graph_tracing,
    graph_tracing_async,
    http_cache_tool,
    http_cache_tool_async,
    mcp_safe_tools,
    mcp_safe_tools_async,
    typed_agent_tools,
    typed_agent_tools_async,
)
from pydantic import BaseModel, Field


# ============================================================================
# R42: graph_retry & graph_retry_async
# ============================================================================

def test_graph_retry_sync():
    attempts = 0

    @graph_retry(max_attempts=3, wait_min=0.01, wait_max=0.05, name="extract_state_node")
    def flaky_node(state: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("LangGraph state sync failure")
        return {"result": state.get("input", "") + "_processed"}

    with agentium.run() as ctx:
        out = flaky_node({"input": "agent_data"})
        assert out == {"result": "agent_data_processed"}
        assert attempts == 3

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    node_calls = [e for e in events if e.payload.get("recipe") == "graph_retry"]
    assert len(node_calls) >= 3
    print("[PASS] test_graph_retry_sync passed.")


def test_graph_retry_async():
    attempts = 0

    @graph_retry_async(max_attempts=2, wait_min=0.01, wait_max=0.05, name="async_node")
    async def async_node(state: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise TimeoutError("Async graph step timeout")
        return {"step": "completed"}

    async def _run():
        res = await async_node({"step": "init"})
        assert res == {"step": "completed"}
        assert attempts == 2

    asyncio.run(_run())
    print("[PASS] test_graph_retry_async passed.")


# ============================================================================
# R43: graph_tracing & graph_tracing_async
# ============================================================================

def test_graph_tracing_sync():
    class MockLangGraph:
        def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return {"output": "workflow_finished", "count": state.get("count", 0) + 1}

    graph = MockLangGraph()
    traced_graph = graph_tracing(graph, name="customer_support_graph")

    with agentium.run() as ctx:
        res = traced_graph.invoke({"count": 5})
        assert res == {"output": "workflow_finished", "count": 6}

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    tracing_events = [e for e in events if e.payload.get("recipe") == "graph_tracing"]
    assert len(tracing_events) == 2
    assert tracing_events[0].payload["graph_name"] == "customer_support_graph"
    print("[PASS] test_graph_tracing_sync passed.")


def test_graph_tracing_async():
    class MockAsyncLangGraph:
        async def ainvoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"async_out": "ok"}

    graph = MockAsyncLangGraph()
    traced = graph_tracing(graph, name="async_workflow")

    async def _run():
        res = await traced.ainvoke({"init": True})
        assert res == {"async_out": "ok"}

    asyncio.run(_run())
    print("[PASS] test_graph_tracing_async passed.")


# ============================================================================
# R44: typed_agent_tools & typed_agent_tools_async
# ============================================================================

class WeatherParams(BaseModel):
    city: str = Field(min_length=2)
    units: str = Field(default="metric")


def test_typed_agent_tools_sync():
    @typed_agent_tools(schema=WeatherParams, effect="read", name="get_weather", description="Get weather for city")
    def get_weather(city: str, units: str = "metric"):
        return f"Weather in {city}: 22C ({units})"

    # 1. Verify schema descriptor
    assert hasattr(get_weather, "openai_schema")
    assert get_weather.openai_schema["type"] == "function"
    assert get_weather.openai_schema["function"]["name"] == "get_weather"
    assert get_weather.__agentium_tool_effect__ == "read"

    # 2. Valid invocation
    with agentium.run():
        res = get_weather(city="Tokyo", units="metric")
        assert res == "Weather in Tokyo: 22C (metric)"

    # 3. Invalid parameter validation
    try:
        get_weather(city="T")  # min_length=2 violated
        assert False, "Expected validation error"
    except ValueError as exc:
        assert "validation failed" in str(exc)

    print("[PASS] test_typed_agent_tools_sync passed.")


def test_typed_agent_tools_async():
    @typed_agent_tools_async(schema=WeatherParams, effect="read", name="async_weather")
    async def async_weather(city: str, units: str = "metric"):
        return f"Async {city}"

    async def _run():
        res = await async_weather(city="Paris")
        assert res == "Async Paris"

    asyncio.run(_run())
    print("[PASS] test_typed_agent_tools_async passed.")


# ============================================================================
# R45: mcp_safe_tools & mcp_safe_tools_async
# ============================================================================

def test_mcp_safe_tools_retry_and_gate():
    reg = ToolRegistry()
    read_attempts = 0

    @tool(effect="read", registry=reg)
    def fetch_inventory():
        nonlocal read_attempts
        read_attempts += 1
        if read_attempts < 2:
            raise ConnectionResetError("Transient MCP transport glitch")
        return {"items": 100}

    @tool(effect="destructive", registry=reg)
    def drop_table(table_name: str):
        return f"Table {table_name} dropped"

    gate = ActionGate(mode="enforce", on_destructive_undeclared="block")
    bridge = mcp_safe_tools(registry=reg, action_gate=gate, max_attempts=3)

    # 1. Read tool retries and succeeds through pybreaker
    with agentium.run():
        res = bridge.call_tool("fetch_inventory")
        assert res == {"items": 100}
        assert read_attempts == 2

    # 2. Destructive tool blocked by ActionGate without human confirmation
    try:
        bridge.call_tool("drop_table", {"table_name": "logs"}, human_confirmed=False)
        assert False, "Expected ActionBlockedError"
    except ActionBlockedError as err:
        assert "blocked by ActionGate" in str(err)

    print("[PASS] test_mcp_safe_tools_retry_and_gate passed.")


def test_mcp_safe_tools_async():
    reg = ToolRegistry()

    @tool(effect="read", registry=reg)
    def async_read():
        return "ok"

    bridge = mcp_safe_tools(registry=reg)

    async def _run():
        res = await bridge.call_tool_async("async_read")
        assert res == "ok"

    asyncio.run(_run())
    print("[PASS] test_mcp_safe_tools_async passed.")


# ============================================================================
# R51: http_cache_tool & http_cache_tool_async
# ============================================================================

def test_http_cache_tool_read_invariance_and_caching():
    # 1. Enforce read effect
    client_cache = http_cache_tool(maxsize=10, ttl=60.0)
    try:
        client_cache.get("https://api.example.com", effect="write")
        assert False, "Expected ValueError on effect='write'"
    except ValueError as exc:
        assert "requires effect='read'" in str(exc)

    # 2. Mock client caching
    calls = 0

    class MockClient:
        def get(self, url, **kwargs):
            nonlocal calls
            calls += 1
            return {"url": url, "data": "fresh_data"}

    cached_client = http_cache_tool(maxsize=10, ttl=60.0, client=MockClient())

    with agentium.run() as ctx:
        # First call: miss
        r1 = cached_client.get("https://api.example.com/v1/users", params={"page": 1})
        assert r1 == {"url": "https://api.example.com/v1/users", "data": "fresh_data"}
        assert calls == 1

        # Second call: hit
        r2 = cached_client.get("https://api.example.com/v1/users", params={"page": 1})
        assert r2 == {"url": "https://api.example.com/v1/users", "data": "fresh_data"}
        assert calls == 1  # Served from cache!

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    hits = [e for e in events if e.payload.get("recipe") == "http_cache_tool" and e.payload.get("cache_hit")]
    assert len(hits) == 1
    print("[PASS] test_http_cache_tool_read_invariance_and_caching passed.")


def test_http_cache_tool_async():
    class MockClient:
        def get(self, url, **kwargs):
            return "async_http_ok"

    client = http_cache_tool(client=MockClient())

    async def _run():
        res = await client.get_async("https://api.example.com/status")
        assert res == "async_http_ok"

    asyncio.run(_run())
    print("[PASS] test_http_cache_tool_async passed.")


# ============================================================================
# R58: fuzzy_dedupe_cache & fuzzy_dedupe_cache_async
# ============================================================================

def test_fuzzy_dedupe_cache_read_invariance_and_near_match():
    # 1. Enforce read effect
    try:
        @fuzzy_dedupe_cache(effect="destructive")
        def delete_fn(q):
            return q
        assert False, "Expected ValueError on destructive tool"
    except ValueError as exc:
        assert "can only be applied to read tools" in str(exc)

    call_count = 0

    @fuzzy_dedupe_cache(threshold=0.88, maxsize=10, ttl=60.0, effect="read")
    def search_knowledge_base(query: str):
        nonlocal call_count
        call_count += 1
        return f"Results for: {query}"

    with agentium.run() as ctx:
        # First call: executes fresh
        res1 = search_knowledge_base("What is Agentium context integrity?")
        assert call_count == 1

        # Second call: near-identical query -> should hit fuzzy dedupe cache!
        res2 = search_knowledge_base("What is Agentium context integrity toolkit?")
        assert call_count == 1
        assert res2 == res1  # Reused cached result!

        # Third call: completely different query -> cache miss
        res3 = search_knowledge_base("How to configure PostgreSQL replication?")
        assert call_count == 2
        assert "PostgreSQL" in res3

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    fuzzy_hits = [e for e in events if e.payload.get("fuzzy_cache_hit")]
    assert len(fuzzy_hits) == 1
    print(f"[PASS] test_fuzzy_dedupe_cache passed (similarity hit recorded).")


def test_fuzzy_dedupe_cache_async():
    calls = 0

    @fuzzy_dedupe_cache_async(threshold=0.85, effect="read")
    async def async_search(text: str):
        nonlocal calls
        calls += 1
        return f"Async {text}"

    async def _run():
        r1 = await async_search("Explain quantum computing basics")
        r2 = await async_search("Explain quantum computing basics.")
        assert r1 == r2
        assert calls == 1

    asyncio.run(_run())
    print("[PASS] test_fuzzy_dedupe_cache_async passed.")


if __name__ == "__main__":
    print("--- R42 graph_retry ---")
    test_graph_retry_sync()
    test_graph_retry_async()

    print("\n--- R43 graph_tracing ---")
    test_graph_tracing_sync()
    test_graph_tracing_async()

    print("\n--- R44 typed_agent_tools ---")
    test_typed_agent_tools_sync()
    test_typed_agent_tools_async()

    print("\n--- R45 mcp_safe_tools ---")
    test_mcp_safe_tools_retry_and_gate()
    test_mcp_safe_tools_async()

    print("\n--- R51 http_cache_tool ---")
    test_http_cache_tool_read_invariance_and_caching()
    test_http_cache_tool_async()

    print("\n--- R58 fuzzy_dedupe_cache ---")
    test_fuzzy_dedupe_cache_read_invariance_and_near_match()
    test_fuzzy_dedupe_cache_async()

    print("\nALL REMAINING TIER 1 RECIPE TESTS PASSED!")
