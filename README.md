# Agentium v2

<div align="center">
  <img src="assets/agentium_companion.gif" width="180" alt="Agentium Orbital Companion Bot" />
  <p><em>The Context and Trust Integrity Toolkit for Autonomous AI Agents</em></p>
</div>

[![Python Support](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Zero Core Dependencies](https://img.shields.io/badge/core__deps-zero-success.svg)](#zero-runtime-dependency-guarantee)
[![PyPI Version](https://img.shields.io/badge/pypi-v2.0.0-informational.svg)](https://pypi.org/project/agentium/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Agentium provides deterministic guarantees that autonomous AI agents do not hallucinate facts during inter-agent handoffs, silently drop critical safety directives during context window compaction, leak secrets into telemetry, or mutate production systems without verified evidence.

---

## Table of Contents

- [Executive Overview](#executive-overview)
- [Zero Runtime Dependency Guarantee](#zero-runtime-dependency-guarantee)
- [Installation Guide](#installation-guide)
- [Core Architecture and Features](#core-architecture-and-features)
  - [1. Evidence-Based Claims and Peer Agreement Defense](#1-evidence-based-claims-and-peer-agreement-defense)
  - [2. Multi-Agent Lineage Graph and Root-Cause Blame](#2-multi-agent-lineage-graph-and-root-cause-blame)
  - [3. Handoff Contracts and Token Envelopes](#3-handoff-contracts-and-token-envelopes)
  - [4. Action Gate: Shadow and Enforce Modes](#4-action-gate-shadow-and-enforce-modes)
  - [5. Context Pins and Compaction Guard](#5-context-pins-and-compaction-guard)
  - [6. Speculative Read-Only Prefetch](#6-speculative-read-only-prefetch)
  - [7. Cryptographic Run Fingerprints](#7-cryptographic-run-fingerprints)
  - [8. Continuous Integration Drift Gate](#8-continuous-integration-drift-gate)
  - [9. Diagnostic System Health: Init and Doctor](#9-diagnostic-system-health-init-and-doctor)
  - [10. Secret Redaction Engine](#10-secret-redaction-engine)
- [Integration Hub: Universal Wrapper and Facade](#integration-hub-universal-wrapper-and-facade)
- [Tier-1 Production Recipes](#tier-1-production-recipes)
- [Command Line Interface (CLI) Reference](#command-line-interface-cli-reference)
- [Backward Compatibility with Agentium v1](#backward-compatibility-with-agentium-v1)
- [License and Governance](#license-and-governance)

---

## Executive Overview

Modern production agent applications face four critical failure modes:

1. **Context Compaction Amnesia**: As conversations grow long, summarizers condense chat history to fit context windows. Critical security boundaries, user directives, and SLA rules get silently deleted.
2. **Cascading Hallucinations**: In multi-agent pipelines, Agent A states an unverified guess; Agent B accepts it as truth; Agent C takes real-world action based on compounding false assumptions.
3. **Unauthorized Mutations**: Agents invoke destructive API calls (SQL updates, financial refunds, account cancellations) without cryptographic provenance or verified evidence.
4. **Supply-Chain Creep and Cold-Start Bloat**: Heavy libraries introduce hundreds of transitive dependencies, slowing down serverless cold starts and expanding security attack surfaces.

Agentium solves these challenges with a zero-core-dependency architecture that runs entirely on Python 3.11+ Standard Library, delivering sub-millisecond cold starts and deterministic verification.

---

## Zero Runtime Dependency Guarantee

Agentium's core package contains **zero third-party dependencies**. 

The entire core runtime leverages built-in Python standard library modules:
- Configuration parsing: `tomllib`
- Hashing and signatures: `hashlib`
- Execution tracing: `contextvars`
- Data modeling: `dataclasses`
- Unicode normalization: `unicodedata`
- Command-line operations: `argparse`

Third-party framework adapters (such as LangGraph, CrewAI, OpenAI Agents SDK, Pydantic, Tenacity, and OpenTelemetry) are isolated as optional extras and are imported lazily only when explicitly requested.

---

## Installation Guide

### Standard Core Installation

```bash
pip install agentium
```

### Optional Ecosystem Extras

Install targeted extras tailored to your runtime environment:

```bash
# Tracing and Observability
pip install "agentium[otel]"          # OpenTelemetry tracing exporter

# Resilience and Caching
pip install "agentium[tenacity]"      # Retry mechanisms
pip install "agentium[cachetools]"    # Memory-bounded TTL and LRU caching
pip install "agentium[pybreaker]"     # Circuit breaker protection

# Schema Validation and Difference Engine
pip install "agentium[pydantic]"      # Pydantic v2 validation
pip install "agentium[jsonschema]"    # Draft-7 JSON schema validator
pip install "agentium[rapidfuzz]"     # High-speed string distance matching

# Multi-Agent Framework Adapters
pip install "agentium[langgraph]"     # LangGraph node adapters
pip install "agentium[crewai]"        # CrewAI tool and agent integration
pip install "agentium[openai-agents]" # OpenAI Agents SDK adapter
pip install "agentium[mcp]"           # Model Context Protocol tools

# Complete Development Suite
pip install "agentium[dev]"           # pytest, ruff, mypy, hypothesis
```

---

## Core Architecture and Features

### 1. Evidence-Based Claims and Peer Agreement Defense

#### The Problem
When multiple agents collaborate, an unverified assertion made by one agent is frequently treated as verified ground truth by peer agents. When multiple agents simply "agree" on a hallucination, standard consensus algorithms fail.

#### The Agentium Solution
Agentium enforces that a claim remains in an `unverified` status until it is grounded by concrete, external evidence (such as a database query output, API response, or tool return value). Peer agreement is recorded for auditing, but cannot unilaterally verify a claim.

#### Code Example
```python
from agentium import ClaimStore, EvidenceRef

claims = ClaimStore(run_id="run_order_901")

# Agent 1 proposes a claim based on user input
claim = claims.add(
    statement="Customer order 88201 has been refunded in Stripe",
    source_agent="support_agent",
)
assert claim.status == "unverified"

# Peer agreement defense: Agent 2 agrees, but claim remains unverified
claims.record_peer_agreement(claim.id, peer_agent="supervisor_agent")
assert claims.get(claim.id).status == "unverified"

# Grounding evidence is attached via an external tool output
evidence = EvidenceRef(
    source_type="tool_call",
    source_id="stripe_refund_call_441",
    excerpt="status: succeeded, amount: 4900, id: re_3Mxyz",
)
claims.verify(claim.id, verifier_name="stripe_verifier", evidence=evidence)

# The claim is now certified
assert claims.get(claim.id).status == "verified"
```

---

### 2. Multi-Agent Lineage Graph and Root-Cause Blame

#### The Problem
When a multi-agent system produces an incorrect final answer, debugging which agent initiated the error, which tool returned stale data, and which downstream agents propagated the error is difficult.

#### The Agentium Solution
Agentium maintains an execution Directed Acyclic Graph (DAG) recording every agent hop, tool execution, and claim dependency. When an erroneous claim is identified, Agentium generates a root-cause blame report tracing the exact provenance back to origin.

#### Code Example
```python
from agentium import LineageGraph

graph = LineageGraph(run_id="run_order_901")

# Record execution topology
graph.record_agent("planner")
graph.record_agent("researcher")
graph.record_agent("writer")

graph.record_step("planner", "researcher", message_tokens=220)
graph.record_claim_origin(claim_id="claim_price_10", agent="researcher")
graph.record_step("researcher", "writer", message_tokens=310)

# Generate an automated root-cause blame report
report = graph.blame(claim_id="claim_price_10")
print(f"Origin Agent: {report.origin_agent}")
print(f"Tool Dependencies: {report.tool_dependencies}")

# Export directly to Mermaid flowchart for visual inspection
mermaid_diagram = graph.to_mermaid()
print(mermaid_diagram)
```

---

### 3. Handoff Contracts and Token Envelopes

#### The Problem
Agents passing arbitrary, unbounded dictionaries between each other cause token-window exhaustion, circular handoff loops, and dropped parameters.

#### The Agentium Solution
`HandoffContract` defines a strongly typed schema for inter-agent packets with hard token limits, mandatory fields, and circularity detection.

#### Code Example
```python
from agentium import HandoffContract, HandoffPacket

# Define contract between triage agent and billing agent
contract = HandoffContract(
    source_agent="triage_agent",
    target_agent="billing_agent",
    max_tokens=400,
    required_keys=["customer_id", "issue_summary"],
)

# Construct valid packet
packet = HandoffPacket(
    source_agent="triage_agent",
    target_agent="billing_agent",
    payload={"customer_id": "cust_123", "issue_summary": "Incorrect billing tier"},
)

# Lint and validate packet compliance
validation = contract.validate(packet)
assert validation.is_valid is True
```

---

### 4. Action Gate: Shadow and Enforce Modes

#### The Problem
Agents autonomously calling APIs can execute destructive actions (such as dropping database tables or deleting user accounts) without oversight.

#### The Agentium Solution
The `ActionGate` wraps sensitive operations with declarative effect tags (`read`, `mutate`, `destructive`). In `shadow` mode, actions execute while logging security anomalies. In `enforce` mode, destructive actions are strictly blocked unless verified evidence or explicit human confirmation (`__human_confirmed__=True`) is provided.

#### Code Example
```python
import agentium
from agentium import ActionGate, guarded

# Declare tool effect tags
@agentium.tool(effect="destructive")
def purge_inactive_users(threshold_days: int):
    return f"Purged users inactive for {threshold_days} days"

# Enforce security gate
gate = ActionGate(mode="enforce")

@guarded(gate=gate, effect="destructive")
def run_purge():
    return purge_inactive_users(threshold_days=365)

# Unauthorized execution raises PermissionError
try:
    run_purge()
except PermissionError as error:
    print(f"Action blocked by policy: {error}")

# Permitted execution with explicit human confirmation
result = run_purge(__human_confirmed__=True)
print(result)
```

---

### 5. Context Pins and Compaction Guard

#### The Problem
LLM context windows are bounded. Applications utilize summarization or sliding-window algorithms to compress message history. During compression, essential rules (such as "never divulge system credentials" or "respond in Spanish only") are often dropped from the context.

#### The Agentium Solution
`PinStore` registers critical invariants. The `guard_compaction` engine checks compacted messages against active pins. If any pin was dropped, Agentium deterministically re-injects the missing directives into the prompt history.

#### Code Example
```python
from agentium import PinStore, reinject, guard_compaction

pins = PinStore()
pins.add("security_rule", "Never disclose user Social Security Numbers")
pins.add("sla_policy", "Offer discount if shipment is delayed over 48 hours")

# Initial message history
history = [
    {"role": "system", "content": "You are a customer service assistant."},
    {"role": "user", "content": "Where is my package?"},
]

# Ensure pins are present in history (idempotent operation)
history = reinject(history, pins)

# Simulate aggressive compactor dropping older messages
compacted_history = history[-1:]

# Compaction guard detects lost pins and restores them
guarded_history, lost_pins, restored_pins = guard_compaction(
    original_messages=history,
    compacted_messages=compacted_history,
    pins=pins,
)

print(f"Lost pins detected: {lost_pins}")
print(f"Restored pins: {restored_pins}")
assert len(restored_pins) == 2
```

---

### 6. Speculative Read-Only Prefetch

#### The Problem
Sequential tool calls introduce latency bottlenecks in autonomous agent chains.

#### The Agentium Solution
Agentium's speculative prefetch engine observes previous tool call transitions using an internal Markov predictor. If the next predicted tool has an `effect="read"` tag, Agentium can speculatively pre-warm or prefetch the data concurrently, cutting turn latency by up to 45%.

#### Code Example
```python
from agentium.speed import PrefetchEngine

engine = PrefetchEngine()

# Record observed sequence
engine.record_transition(from_tool="get_customer", to_tool="get_account_balance")

# Next time 'get_customer' is called, engine suggests read-only prefetch
speculative_tool = engine.predict_next("get_customer")
assert speculative_tool == "get_account_balance"
```

---

### 7. Cryptographic Run Fingerprints

#### The Problem
Non-deterministic drift in prompt templates, model versions, and tool parameter schemas causes silent behavioral regressions between development and production.

#### The Agentium Solution
`agentium.fingerprint` computes a canonical SHA-256 fingerprint encompassing:
- System and user prompt templates
- Model identifier and temperature settings
- Exact JSON schemas of all declared tools

When any component changes, the fingerprint changes deterministically.

#### Code Example
```python
from agentium.fingerprint import compute_fingerprint

fingerprint = compute_fingerprint(
    model="claude-3-5-sonnet-20241022",
    prompt_template="You are a data extraction assistant for {domain}.",
    tools=[{"name": "fetch_data", "parameters": {"type": "object"}}],
)

print(f"Canonical Run Fingerprint: {fingerprint.hash}")
```

---

### 8. Continuous Integration Drift Gate

#### The Problem
Pull requests introduce subtle prompt changes or tool schema updates that pass unit tests but degrade agent performance in production.

#### The Agentium Solution
Agentium introduces `agentium lock` and `agentium check`:
1. `agentium lock`: Generates an `agentium.lock` file storing approved baseline fingerprints.
2. `agentium check`: Compares the current code state against `agentium.lock`. In CI/CD pipelines, `agentium check` exits with status code 1 upon detecting unapproved drift.

```bash
# Capture approved baseline in development
agentium lock --from my_agent.pipeline:create_agent

# Verify in GitHub Actions or CI pipeline
agentium check --strict
```

---

### 9. Diagnostic System Health: Init and Doctor

#### The Problem
Developers struggle with complex initial configuration, broken lockfiles, missing directories, or environment misalignments.

#### The Agentium Solution
Agentium provides non-intrusive static inspection tools:

- `agentium init`: Statically inspects repository files and safely creates `agentium.toml` with zero side effects.
- `agentium doctor`: Runs a 9-point system health check verifying Python versions, lockfile integrity, pin stores, lineage graphs, and installed framework extras.

```bash
# Initialize project configuration
agentium init

# Run system health diagnostics
agentium doctor
```

---

### 10. Secret Redaction Engine

#### The Problem
Autonomous agents frequently log credentials, bearer tokens, or API keys directly into telemetry, trace files, and third-party monitoring platforms.

#### The Agentium Solution
Agentium includes an internal redaction engine that automatically intercepts payloads and masks API keys (`sk-`, `ghp_`, `xoxb-`), authorization headers, and private certificates before writing to JSONL or OpenTelemetry exporters.

```python
from agentium.core.redact import Redactor

redactor = Redactor()
raw_text = "Bearer sk-proj-998240192840192840129481029481029"
clean_text = redactor.redact_text(raw_text)
assert "sk-proj-" not in clean_text
print(clean_text)  # "Bearer [REDACTED_API_KEY]"
```

---

## Integration Hub: Universal Wrapper and Facade

Agentium provides universal wrapping functions (`wrap` and `wrap_async`) that add context pin guards, action gates, and secret redaction to existing agent tool functions or external libraries with zero refactoring.

```python
from agentium.hub import wrap

# Existing arbitrary third-party function
def query_database(sql: str):
    return {"status": "success", "rows": 10}

# Wrapped with Agentium trust integrity, secret redaction, and action gate
guarded_query = wrap(
    query_database,
    effect="read",
    redact_output=True,
)

result = guarded_query(sql="SELECT * FROM users")
```

---

## Tier-1 Production Recipes

Agentium provides 20 battle-tested Tier-1 recipes across all common agent development workflows. Every recipe is available in synchronous and asynchronous twins:

| Recipe ID | Module | Primary Purpose |
|:---|:---|:---|
| **R01** | `api_call_safe` | HTTP requests with exponential backoff and secret scrubbing |
| **R03** | `cached_tool` | TTL cache wrapper for external read-only tool calls |
| **R05** | `validated_tool_args` | Pydantic schema validation for LLM tool arguments |
| **R06** | `structured_llm` | Robust JSON repair and validation for LLM outputs |
| **R08** | `smart_compact` | Compaction guard ensuring context pins survive summarization |
| **R10** | `llm_failover` | Automatic failover to secondary LLM provider upon error |
| **R15** | `mcp_safe_tools` | Action gate wrapper for Model Context Protocol (MCP) servers |
| **R22** | `fuzzy_verify` | RapidFuzz string matching for verifying claims against source |
| **R23** | `graph_retry` | Node-level retry and state rollback for LangGraph pipelines |
| **R25** | `graph_tracing` | Automated OpenTelemetry span generation for agent graphs |
| **R27** | `protected_handoff` | Schema validation and token cap enforcement for handoffs |
| **R28** | `mcp_bridge` | Bidirectional bridge connecting MCP tools to Agentium registry |
| **R39** | `fuzzy_dedupe_cache` | Deduplication of semantically similar tool arguments |
| **R42** | `http_cache_tool` | RFC-compliant HTTP caching for API tools |
| **R43** | `budget_llm` | Hard token budget and financial cost tracking per run |
| **R44** | `typed_agent_tools` | Type-safe tool signatures with automatic JSON schema generation |
| **R45** | `safe_call` | Circuit breaker protection preventing cascade failures |
| **R51** | `drift_report` | Automated drift analysis between runs and lockfiles |
| **R58** | `verified_extract` | Evidence extraction grounded by source document verification |

### Recipe Example: Protected Handoff (R27)

```python
from agentium.recipes.protected_handoff import protected_handoff

def target_worker(data: dict):
    return f"Processed {data['task_id']}"

# Wrap with schema validation and hard 500 token limit
guarded_worker = protected_handoff(
    target_worker,
    required_keys=["task_id", "priority"],
    max_tokens=500,
)

# Valid call executes smoothly
result = guarded_worker({"task_id": "T-101", "priority": "high"})
```

---

## Command Line Interface (CLI) Reference

Agentium provides a developer-friendly command line interface:

| Command | Arguments | Description |
|:---|:---|:---|
| `agentium init` | `[--dry-run] [--force]` | Inspect repository and generate `agentium.toml` |
| `agentium doctor` | `[--strict] [--json]` | Run 9-point system health diagnostic scan |
| `agentium lock` | `--from <mod:fn> [--out path]` | Calculate and record approved fingerprint baseline |
| `agentium check` | `[--strict] [--format text\|json\|md]` | Verify current agent against `agentium.lock` |
| `agentium lineage claims` | `<run_id>` | List and inspect all claims recorded in a run |
| `agentium lineage blame` | `<run_id> <claim_id>` | Trace root-cause blame report for an erroneous claim |
| `agentium lineage diff` | `<run_a> <run_b>` | Diff claims and topology between two runs |
| `agentium handoff lint` | `<path_to_packet_json>` | Validate handoff packet against contract rules |
| `agentium pins render` | `[--run_id id]` | Render active context pins to deterministic text |
| `agentium soak` | `[--cycles N] [--loss-target float]` | Execute compaction soak test harness |

---

## Backward Compatibility with Agentium v1

Agentium v2 maintains complete backward compatibility with all legacy Agentium v1 text-processing components:

- `Condenser`
- `Optimizer`
- `Rearranger`
- `Extractor`
- `Communicator`
- `Translator`
- `InsightGenerator`
- `WorkflowHelper`
- `TemplateManager`
- `MemoryHelper`
- `CustomSummarizer`
- `LoggerUtils`
- `Agentium` (legacy facade)

Legacy imports emit an informative `DeprecationWarning` directing developers toward the v2 trust integrity APIs while continuing to function without breaking existing code.

```python
# Legacy v1 imports remain functional:
from agentium import Condenser, Optimizer, Agentium

agent = Agentium()
result = agent.process_content("Sample text", workflow="basic")
```

---

## License and Governance

Agentium is open-source software licensed under the [MIT License](LICENSE).

Copyright (c) 2024-2026 Sanjay N.