# Agentium v2

[![Python Support](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Zero Dependencies](https://img.shields.io/badge/core_deps-zero-success.svg)](#zero-runtime-dependency-pledge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Context & trust integrity toolkit for multi-agent and long-running AI agents.**

Agentium guarantees that AI agents don't hallucinate facts during handoffs, silently drop critical instructions during context-window compaction, leak API credentials into telemetry, or mutate production systems without verified evidence.

---

## ⚡ Key Highlights

- 🔒 **Zero Core Dependencies**: Core runtime uses **Python 3.11+ Standard Library only**. No bloated dependency trees, no supply-chain vulnerability creep, sub-millisecond cold starts.
- 📌 **Context Pins (F5)**: Critical directives, SLAs, and security rules survive context compaction via deterministic, idempotent re-injection.
- 🛡️ **Action Gate (F4)**: Prevent unauthorized mutations. Destructive actions require human confirmation or verified grounding evidence.
- 🤝 **Evidence-Based Claims & Peer Agreement Defense (F1)**: Claims require grounded evidence. Peer agents cannot self-certify unverified statements.
- 📊 **Multi-Agent Lineage Graph (F2)**: Full provenance DAG with root-cause blame reports and automatic Mermaid flowchart generation.
- 📦 **Handoff Contracts (F3)**: Structured packets between agents with hard token caps and unbreakable constraints.
- 🧬 **Run Fingerprints & Drift CI Gate (F7, F8)**: Cryptographically lock agent prompts, models, and schemas (`agentium lock`). Fail CI pull requests on drift (`agentium check`).
- 🩺 **Developer Health (F9)**: Non-intrusive static scan (`agentium init`) and 9-point system health check (`agentium doctor`).
- ⚡ **Speculative Prefetch (F10)**: Experimental read-only prefetch engine with Markov chain next-tool prediction.

---

## 🚀 Quickstart

### 1. Installation

```bash
# Core library (Zero third-party runtime dependencies)
pip install agentium

# Optional extras
pip install "agentium[otel]"          # OpenTelemetry tracing export
pip install "agentium[langgraph]"     # LangGraph adapter
pip install "agentium[crewai]"        # CrewAI adapter
pip install "agentium[openai-agents]" # OpenAI Agents SDK adapter
```

### 2. Initialize in your project

```bash
# Statically inspects project files and generates agentium.toml
agentium init

# Run system health diagnostics
agentium doctor
```

### 3. Declaring Tools & Effect Tags

```python
import agentium

# Read tools are always safe
@agentium.tool(effect="read")
def lookup_customer(customer_id: str):
    return {"id": customer_id, "plan": "enterprise"}

# Destructive tools require authorization
@agentium.tool(effect="destructive")
def terminate_subscription(customer_id: str):
    return f"Terminated {customer_id}"
```

### 4. Protecting Long-Running Agents with Context Pins

```python
from agentium import PinStore, reinject, guard_compaction

# Register non-negotiable boundaries
pins = PinStore()
pins.add("security_boundary", "Never execute SQL DROP or DELETE operations")
pins.add("customer_sla", "Respond within 15 minutes")

# Inject pins into messages before model calls (idempotent no-op if already present)
messages = [{"role": "user", "content": "Help with account"}]
messages = reinject(messages, pins)

# When compaction drops older history, guard_compaction restores active pins
compacted_messages = messages[-2:]  # Aggressive compactor
repaired, lost, restored = guard_compaction(messages, compacted_messages, pins)
print(f"Pins recovered: {restored}")
```

### 5. Multi-Agent Claims & Provenance Blame

```python
from agentium import ClaimStore, EvidenceRef, LineageGraph

claims = ClaimStore(run_id="run_101")

# Agent 1 proposes an unverified statement
c1 = claims.add("Payment transaction approved", source_agent="billing_agent")

# Peer agreement defense: Agent 2 agreeing does NOT mark it verified
claims.record_peer_agreement(c1.id, peer_agent="fulfillment_agent")
assert claims.get(c1.id).status == "unverified"

# Grounding evidence verifies the claim
evidence = EvidenceRef(
    source_type="tool_call",
    source_id="stripe_charge_42",
    excerpt="Charge status: succeeded",
)
claims.verify(c1.id, verifier_name="stripe_verifier", evidence=evidence)
assert claims.get(c1.id).status == "verified"
```

### 6. Action Gate (Shadow & Enforce Modes)

```python
from agentium import ActionGate, guarded

gate = ActionGate(mode="enforce")

@guarded(gate=gate, effect="destructive")
def wipe_database():
    return "Database wiped"

# Blocked by default in enforce mode
try:
    wipe_database()
except PermissionError as e:
    print(f"Action blocked: {e}")

# Permitted with human confirmation
wipe_database(__human_confirmed__=True)
```

---

## 🛠️ CLI Reference

Agentium provides a CLI for CI/CD gates, diagnostics, and debugging:

| Command | Description |
|:---|:---|
| `agentium init [--dry-run] [--force]` | Statically scan project files and generate `agentium.toml` |
| `agentium doctor [--strict] [--json]` | 9-point health check (Python, lock, pins, lineage, scanners) |
| `agentium lock --from <mod:fn>` | Record baseline model, prompt, and tool schema fingerprint to `agentium.lock` |
| `agentium check [--format text\|json\|md]` | Verify current agent against `agentium.lock`; exit 0 (match) or 1 (drift) |
| `agentium lineage claims <run_id>` | Inspect claims generated in a run |
| `agentium lineage blame <run_id> <claim_id>` | Trace claim root-cause back to origin agent, tools, and dependencies |
| `agentium lineage diff <run_a> <run_b>` | Diff claims and handoff topology between two runs |
| `agentium handoff lint <path>` | Lint handoff packet JSON against schema, circular handoffs, and limits |
| `agentium pins render` | Render deterministic text block of active context pins |
| `agentium soak` | Run compaction soak test simulating 20+ multi-turn compactions |

---

## 🔒 Zero Runtime Dependency Pledge

The core package of Agentium v2 has **zero third-party dependencies**. It relies exclusively on the Python Standard Library (`tomllib`, `hashlib`, `unicodedata`, `contextvars`, `dataclasses`, `argparse`).

To verify:
```bash
python -c "import agentium; print('Zero external modules imported!')"
```

---

## 🔄 Backward Compatibility with v1

All legacy v1 public classes (`Condenser`, `Optimizer`, `Rearranger`, `Communicator`, `Extractor`, `Translator`, etc.) and integration shims (`agentium.integrations.gemini`) remain fully operational and tested. They emit a `DeprecationWarning` directing users to the v2 context and trust integrity APIs.

```python
# Legacy v1 usage continues to function:
from agentium import Condenser  # Emits DeprecationWarning
```

---

## 📄 License

MIT License. Copyright (c) 2024-2026 Sanjay N.