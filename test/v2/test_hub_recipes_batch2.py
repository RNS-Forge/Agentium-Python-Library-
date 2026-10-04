"""Tests for Agentium Batch 2 Integration Recipes (R10, R23, R15, R02, R25)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Dict

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import agentium
from agentium.adapters.plain import ToolRegistry, tool
from agentium.core.events import EventReader, EventType
from agentium.lineage.claims import ClaimStore
from agentium.lineage.gate import ActionBlockedError, ActionGate
from agentium.pin.store import PinStore
from agentium.recipes import (
    mcp_bridge,
    mcp_bridge_async,
    protected_handoff,
    protected_handoff_async,
    smart_compact,
    smart_compact_async,
    structured_llm,
    structured_llm_async,
    validated_tool_args,
    validated_tool_args_async,
)
from pydantic import BaseModel, Field


# ============================================================================
# R10: protected_handoff & protected_handoff_async
# ============================================================================

class UserHandoffContext(BaseModel):
    user_id: int
    intent: str


def test_protected_handoff_pydantic_and_redaction():
    raw_context = [
        {"user_id": 101, "intent": "refund", "secret_key": "sk-1234567890abcdef1234567890"},
    ]

    with agentium.run() as ctx:
        packet = protected_handoff(
            from_agent="support_agent",
            to_agent="billing_agent",
            task="Process customer refund request",
            context=raw_context,
            schema=UserHandoffContext,
            redact=True,
        )

        assert packet.from_agent == "support_agent"
        assert packet.to_agent == "billing_agent"
        assert len(packet.context) == 1
        assert packet.context[0]["user_id"] == 101
        # Check secret was redacted
        assert packet.context[0]["secret_key"] == "[REDACTED_API_KEY]"

    reader = EventReader(run_id=ctx.run_id, events_dir=ctx.writer.events_dir)
    events = list(reader)
    handoff_events = [e for e in events if e.type == EventType.HANDOFF.value]
    assert len(handoff_events) == 1
    assert handoff_events[0].payload["from_agent"] == "support_agent"
    print("[PASS] test_protected_handoff_pydantic_and_redaction passed.")


def test_protected_handoff_jsonschema_validation():
    schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "page": {"type": "integer"},
        },
        "required": ["query", "page"],
    }

    # Valid
    packet = protected_handoff(
        from_agent="orchestrator",
        to_agent="searcher",
        task="Execute web search",
        context=[{"query": "antigravity ai", "page": 1}],
        schema=schema,
    )
    assert len(packet.context) == 1

    # Invalid
    try:
        protected_handoff(
            from_agent="orchestrator",
            to_agent="searcher",
            task="Execute web search",
            context=[{"query": "antigravity ai", "page": "not_an_int"}],
            schema=schema,
        )
        assert False, "Expected validation failure for invalid schema"
    except Exception:
        print("[PASS] Invalid schema rejected as expected.")


def test_protected_handoff_async_twin():
    async def _run():
        packet = await protected_handoff_async(
            from_agent="agent_a",
            to_agent="agent_b",
            task="Sync handoff task",
            context=[{"user_id": 99, "intent": "upgrade"}],
            schema=UserHandoffContext,
        )
        assert packet.task == "Sync handoff task"

    asyncio.run(_run())
    print("[PASS] test_protected_handoff_async_twin passed.")


# ============================================================================
# R23: validated_tool_args & validated_tool_args_async
# ============================================================================

class SearchQueryModel(BaseModel):
    query: str = Field(min_length=2)
    max_results: int = Field(default=10, ge=1, le=100)


def test_validated_tool_args_pydantic():
    @validated_tool_args(schema=SearchQueryModel, effect="read", name="search_db")
    def search_db(query: str, max_results: int = 10):
        return f"Results for '{query}' (limit {max_results})"

    # Valid call
    with agentium.run() as ctx:
        res = search_db(query="python", max_results=5)
        assert res == "Results for 'python' (limit 5)"

    # Invalid call (max_results > 100)
    with agentium.run() as ctx:
        try:
            search_db(query="python", max_results=500)
            assert False, "Expected ValueError on validation failure"
        except ValueError as err:
            assert "validation failed" in str(err)

    print("[PASS] test_validated_tool_args_pydantic passed.")


def test_validated_tool_args_async_twin():
    @validated_tool_args_async(schema=SearchQueryModel, effect="read", name="async_search")
    async def async_search(query: str, max_results: int = 10):
        await asyncio.sleep(0.01)
        return [f"doc_{i}" for i in range(max_results)]

    async def _run():
        res = await async_search("ai tools", max_results=3)
        assert len(res) == 3

    asyncio.run(_run())
    print("[PASS] test_validated_tool_args_async_twin passed.")


# ============================================================================
# R15: smart_compact & smart_compact_async
# ============================================================================

def test_smart_compact_pin_preservation():
    store = PinStore(run_id="compact_test_run")
    store.add(key="CORE_RULE", text="Never expose customer credentials to external systems.")
    store.add(key="OUTPUT_FORMAT", text="Always respond in valid Markdown.")

    # Create message chain with 10 intermediate messages
    messages = [{"role": "system", "content": "You are a helpful banking assistant."}]
    for i in range(12):
        messages.append({"role": "user", "content": f"Turn {i}: What is the interest rate for savings account?"})
        messages.append({"role": "assistant", "content": f"Turn {i}: The current interest rate is 3.5% APY."})

    # Total tokens will be large; request max_tokens=150
    compacted, tokens_before, tokens_after = smart_compact(
        messages=messages,
        pin_store=store,
        max_tokens=150,
        keep_last_n=2,
    )

    assert tokens_after < tokens_before
    # Verify that the rendered pins survived compaction!
    compacted_text = " ".join(str(m["content"]) for m in compacted)
    assert "Never expose customer credentials" in compacted_text
    assert "Always respond in valid Markdown" in compacted_text
    print(f"[PASS] test_smart_compact_pin_preservation passed (Tokens: {tokens_before} -> {tokens_after}).")


def test_smart_compact_async_twin():
    async def _run():
        store = PinStore(run_id="compact_async_run")
        store.add(key="IMPORTANT", text="Active Pin Text")
        msgs = [
            {"role": "system", "content": "System prompt."},
            {"role": "user", "content": "User question."},
        ]
        compacted, _, _ = await smart_compact_async(msgs, store, max_tokens=500)
        assert len(compacted) >= 2

    asyncio.run(_run())
    print("[PASS] test_smart_compact_async_twin passed.")


# ============================================================================
# R02: structured_llm & structured_llm_async
# ============================================================================

class ExtractedEntity(BaseModel):
    name: str
    category: str
    confidence: float


def test_structured_llm_with_broken_json_repair():
    # Simulate an LLM producing broken/truncated JSON (single quotes, trailing comma, unclosed bracket)
    broken_llm_output = "{'name': 'Agentium', 'category': 'AI Framework', 'confidence': 0.99,"

    def mock_llm(prompt: str) -> str:
        return broken_llm_output

    with agentium.run() as ctx:
        result = structured_llm(
            prompt="Extract entity info",
            model_cls=ExtractedEntity,
            llm_callable=mock_llm,
        )

        assert isinstance(result, ExtractedEntity)
        assert result.name == "Agentium"
        assert result.category == "AI Framework"
        assert result.confidence == 0.99

    print("[PASS] test_structured_llm_with_broken_json_repair successfully repaired broken JSON.")


def test_structured_llm_async_twin():
    async def mock_async_llm(prompt: str) -> str:
        await asyncio.sleep(0.01)
        return "{'name': 'V2_Engine', 'category': 'Core', 'confidence': 1.0}"

    async def _run():
        res = await structured_llm_async(
            prompt="Extract entity",
            model_cls=ExtractedEntity,
            async_llm_callable=mock_async_llm,
        )
        assert res.name == "V2_Engine"
        assert res.confidence == 1.0

    asyncio.run(_run())
    print("[PASS] test_structured_llm_async_twin passed.")


# ============================================================================
# R25: mcp_bridge & mcp_bridge_async
# ============================================================================

def test_mcp_bridge_listing_and_action_gate():
    reg = ToolRegistry()

    @tool(effect="read", registry=reg)
    def get_metric(metric_name: str) -> int:
        """Fetch system metric."""
        return 42

    @tool(effect="destructive", registry=reg)
    def purge_record(record_id: str) -> str:
        """Purge customer record."""
        return f"Record {record_id} deleted."

    gate = ActionGate(mode="enforce", on_destructive_undeclared="block")
    bridge = mcp_bridge(registry=reg, action_gate=gate)

    # 1. Test MCP listing
    tools_list = bridge.list_tools()
    assert len(tools_list) == 2
    tool_names = [t["name"] for t in tools_list]
    assert "get_metric" in tool_names
    assert "purge_record" in tool_names
    # Check effect tag in MCP metadata
    purge_meta = [t for t in tools_list if t["name"] == "purge_record"][0]["metadata"]
    assert purge_meta["effect"] == "destructive"

    # 2. Test Safe Read dispatch through MCP
    with agentium.run():
        val = bridge.call_tool("get_metric", {"metric_name": "cpu_load"})
        assert val == 42

    # 3. Test Destructive tool blocked by ActionGate without human confirmation
    try:
        bridge.call_tool("purge_record", {"record_id": "rec_001"}, human_confirmed=False)
        assert False, "Expected ActionBlockedError on destructive MCP tool call"
    except ActionBlockedError as exc:
        assert "blocked by ActionGate" in str(exc)
        print("[PASS] Destructive MCP tool call blocked as expected.")

    # 4. Test Destructive tool permitted with human confirmation
    confirmed_res = bridge.call_tool("purge_record", {"record_id": "rec_001"}, human_confirmed=True)
    assert confirmed_res == "Record rec_001 deleted."

    print("[PASS] test_mcp_bridge_listing_and_action_gate passed.")


def test_mcp_bridge_async_twin():
    reg = ToolRegistry()

    @tool(effect="read", registry=reg)
    def read_config():
        return {"env": "production"}

    bridge = mcp_bridge(registry=reg)

    async def _run():
        res = await bridge.call_tool_async("read_config")
        assert res == {"env": "production"}

    asyncio.run(_run())
    print("[PASS] test_mcp_bridge_async_twin passed.")


if __name__ == "__main__":
    print("--- R10 protected_handoff ---")
    test_protected_handoff_pydantic_and_redaction()
    test_protected_handoff_jsonschema_validation()
    test_protected_handoff_async_twin()

    print("\n--- R23 validated_tool_args ---")
    test_validated_tool_args_pydantic()
    test_validated_tool_args_async_twin()

    print("\n--- R15 smart_compact ---")
    test_smart_compact_pin_preservation()
    test_smart_compact_async_twin()

    print("\n--- R02 structured_llm ---")
    test_structured_llm_with_broken_json_repair()
    test_structured_llm_async_twin()

    print("\n--- R25 mcp_bridge ---")
    test_mcp_bridge_listing_and_action_gate()
    test_mcp_bridge_async_twin()

    print("\nALL BATCH 2 RECIPE TESTS PASSED!")
