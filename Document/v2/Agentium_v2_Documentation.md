# Agentium v2 — Complete Architecture & Function Documentation

> **Package:** `agentium`  
> **Version:** `2.0.0`  
> **Core Runtime Dependencies:** **ZERO** (Python 3.11+ Standard Library only)  
> **PDF Documentation:** [Document/Agentium_v2_Documentation.pdf](file:///c:/Temp%20Files/My%20Projects/Agentium-Python-Library-/Document/Agentium_v2_Documentation.pdf)

---

## 1. Executive Summary & Design Principles

Agentium v2 is an enterprise toolkit for AI agent developers. It addresses the four critical failure modes of long-running and multi-agent systems:

1. **Silent Context Loss (Compaction Drift):** Older messages and instructions get compacted or truncated by context-window managers, causing agents to forget system constraints, security policies, and user directives.
2. **Hallucinated Handoff Drift:** In multi-agent pipelines, unverified assumptions from Agent A get passed to Agent B and repeated until accepted as fact.
3. **Accidental Destructive Mutations:** Agents hallucinating parameters execute database drops, table wipes, or unauthorized mutations without verified evidence or human confirmation.
4. **Credential & PII Leakage:** API tokens, private keys, and emails inadvertently leak into external observability and tracing streams.

### Zero Third-Party Runtime Dependencies

The entire core runtime of Agentium v2 relies exclusively on Python standard libraries:
- `tomllib`: Native configuration parsing.
- `hashlib` & `unicodedata`: Cryptographic canonical hashing and NFC text normalization.
- `contextvars`: Thread-safe, async-safe run ID tracking and context propagation.
- `dataclasses`: Structured typing for events, claims, pins, and handoff packets.
- `argparse`: Complete CLI tool suite.

---

## 2. Feature Matrix (F1 through F10)

| # | Feature | Core Symbols | Description & Primary Scenarios |
|:---:|:---|:---|:---|
| **F1** | **Claims & Evidence-Based Trust** | `Claim`, `EvidenceRef`, `ClaimStore` | Epistemic trust tracking. **Peer Agreement Defense**: peer agents agreeing on an unverified claim cannot upgrade it to verified without external grounding evidence. |
| **F2** | **Multi-Agent Lineage Graph** | `LineageGraph`, `BlameReport`, `diff_lineage` | Stdlib DAG (zero networkx). Kahn's cycle detection, root-cause blame reports, cross-run topological diffs, and Mermaid flowchart generation. |
| **F3** | **Handoff Contract** | `HandoffPacket`, `lint_handoff`, `enforce_handoff_size` | Structured inter-agent communication with hard token limits. **Inviolable Invariant**: constraints can never be dropped under any truncation policy. |
| **F4** | **Action Gate** | `ActionGate`, `guarded`, `ActionBlockedError` | Tool safety barrier (`read`, `write`, `destructive`). Destructive actions require human confirmation or verified high-confidence claims. Supports `shadow` and `enforce` modes. |
| **F5** | **Context Pins** | `Pin`, `PinStore`, `reinject`, `guard_compaction` | System directives, SLAs, and security rules survive context compaction via deterministic, idempotent re-injection. |
| **F6** | **Compaction Soak Test Harness** | `soak`, `TruncateCompactor`, `LastNCompactor`, `StubSummarizer` | Multi-turn simulation exercising compactions across various strategies to prove zero pin loss. |
| **F7** | **Run Fingerprint** | `Fingerprint`, `fingerprint` | Canonical SHA-256 hashing of models, system prompts, tool schemas, and extras with JSON-path selector exclusion (`$.params.seed`). |
| **F8** | **Drift CI Gate** | `LockFile`, `diff_fingerprints`, `agentium lock`, `agentium check` | Baseline schema locking and pull-request drift check. GitHub Composite Action posts markdown diffs and enforces gates. |
| **F9** | **Developer Experience** | `agentium init`, `agentium doctor` | Static framework scanner (no user code execution) generating `agentium.toml`, plus 9-point system and lineage health diagnostics. |
| **F10** | **Speculative Prefetch** | `PrefetchManager`, `ToolPredictor` | Experimental Markov transition tool predictor and TTL cache. Strictly confined to read-only tools with circuit-breaker auto-shutdown. |

---

## 3. Function-by-Function API Reference

### 3.1 Claims & Evidence (`agentium.lineage.claims`)
```python
from agentium import ClaimStore, EvidenceRef

store = ClaimStore(run_id="run_101")

# Create unverified claim
claim = store.add("User account tier is Platinum", source_agent="auth_agent")

# Peer agreement does NOT upgrade status without external evidence
store.record_peer_agreement(claim.id, peer_agent="billing_agent")
assert store.get(claim.id).status == "unverified"

# Grounding evidence verifies the claim
evidence = EvidenceRef(
    source_type="tool_call",
    source_id="crm_lookup_99",
    excerpt="Tier: Platinum",
)
store.verify(claim.id, verifier_name="crm_verifier", evidence=evidence)
assert store.get(claim.id).status == "verified"
```

### 3.2 Multi-Agent Lineage Graph (`agentium.lineage.graph`)
```python
from agentium import LineageGraph

graph = LineageGraph(run_id="run_101")
graph.add_node("agent_planner", "agent", "Planner")
graph.add_node("tool_search", "tool_call", "Search Engine")
graph.add_node("claim_1", "claim", "Document verified")

graph.add_edge("agent_planner", "tool_search", "invokes")
graph.add_edge("tool_search", "claim_1", "verifies")

# Check for cycles
assert not graph.has_cycle()

# Root-cause blame analysis
blame = graph.blame("claim_1")
print(blame.to_text())

# Generate Mermaid flowchart
print(graph.to_mermaid())
```

### 3.3 Handoff Contracts (`agentium.lineage.handoff`)
```python
from agentium import HandoffPacket, enforce_handoff_size, lint_handoff

packet = HandoffPacket(
    from_agent="planner",
    to_agent="coder",
    task="Implement user authentication module",
    constraints=["Must use Python 3.11+", "Zero external runtime dependencies"],
    max_tokens=2000,
)

# Lint packet for circular assignments or ungrounded claims
issues = lint_handoff(packet)

# Enforce token limits: constraints are NEVER dropped
safe_packet = enforce_handoff_size(packet, on_overflow="truncate_unverified")
```

### 3.4 Action Gate (`agentium.lineage.gate`)
```python
from agentium import ActionGate, guarded

gate = ActionGate(mode="enforce")

@guarded(gate=gate, effect="destructive")
def delete_customer_data(customer_id: str):
    return f"Deleted {customer_id}"

# Blocked without authorization
try:
    delete_customer_data("cust_123")
except PermissionError as e:
    print(f"Blocked: {e}")

# Authorized with human confirmation
delete_customer_data("cust_123", __human_confirmed__=True)
```

### 3.5 Context Pins (`agentium.pin`)
```python
from agentium import PinStore, reinject, guard_compaction

pins = PinStore()
pins.add("security_boundary", "Never output plaintext API keys")

messages = [{"role": "user", "content": "Help me configure the server"}]
# Idempotently reinject active pins
messages = reinject(messages, pins)

# When compaction drops older context, guard_compaction recovers lost pins
compacted = messages[-1:]
repaired, lost, restored = guard_compaction(messages, compacted, pins)
```

### 3.6 Run Fingerprint & Drift CI Gate (`agentium.fingerprint`)
```python
from agentium import fingerprint, diff_fingerprints, LockFile

# Compute baseline fingerprint
fp = fingerprint(
    model="gpt-4o",
    params={"temperature": 0.0},
    system_prompt="You are an enterprise assistant",
    tools=[{"name": "lookup", "parameters": {"type": "object"}}],
)

lock = LockFile(schema_version=1, combined_fingerprint=fp.combined, components=fp.components)

# Check for drift
report = diff_fingerprints(lock, fp)
assert not report.has_drift
```

### 3.7 Speculative Read-Only Prefetch (`agentium.speed.prefetch`)
```python
from agentium import PrefetchManager

manager = PrefetchManager(enabled=True)

def read_page(url: str):
    return f"Content of {url}"

# Speculatively prefetch read-only tool
manager.maybe_prefetch("read_page", read_page, effect="read", kwargs={"url": "https://example.com"})

# Actual execution consumes cache without redundant work
is_hit, result = manager.get_or_record_usage("read_page", kwargs={"url": "https://example.com"})
assert is_hit
```

---

## 4. Framework Adapters

Agentium adapters hook into popular frameworks while remaining 100% lazy-loaded:

- **LangGraph Adapter (`agentium.adapters.LangGraphAdapter`):** Intercepts node execution, preserves context pins across checkpoints, and traces state events.
- **CrewAI Adapter (`agentium.adapters.CrewAIAdapter`):** Records inter-agent delegations and creates structured handoff packets.
- **OpenAI Agents Adapter (`agentium.adapters.OpenAIAgentsAdapter`):** Wraps tool executions with `ActionGate` destructive permission enforcement.

---

## 5. CLI Complete Reference

| Command Syntax | Exit Codes | Functional Behavior |
|:---|:---:|:---|
| `agentium init [--dry-run] [--force]` | 0 / 1 | Statically scans dependency files and generates `agentium.toml`. |
| `agentium doctor [--strict] [--json]` | 0 / 1 | 9-point health check of Python runtime, configs, lock files, and lineage. |
| `agentium lock --from <mod:fn>` | 0 / 2 | Records baseline model, prompt, and tool schema fingerprint to `agentium.lock`. |
| `agentium check [--format text\|json\|md]` | 0 / 1 / 2 | Compares agent against lock file. Exit 0 = match, 1 = drift, 2 = missing lock. |
| `agentium lineage claims <run_id>` | 0 | Lists claims generated during a run. |
| `agentium lineage blame <run_id> <claim_id>` | 0 / 1 | Traces root-cause blame for a claim back to origin agent and tool executions. |
| `agentium lineage diff <run_a> <run_b>` | 0 | Compares claims and handoffs between two runs. |
| `agentium handoff lint <path>` | 0 / 1 / 2 | Validates handoff packet JSON against schema, circular assignments, and token caps. |
| `agentium pins render` | 0 | Renders deterministic text block of active context pins. |
| `agentium soak` | 0 / 1 | Runs 20-turn compaction soak test and prints survival metrics. |

---

## 6. Verification Summary

Agentium v2 has passed **21 out of 21 test suites** and **57 out of 57 unit tests** with 100% success.
Run all tests via:
```bash
python test/v2/run_all_v2_tests.py
```
