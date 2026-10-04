# Changelog

All notable changes to Agentium will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-10-04

### Architecture & Major Highlights
- **Zero Third-Party Runtime Dependencies**: The entire core runtime of Agentium v2 relies strictly on Python 3.11+ Standard Library (`tomllib`, `hashlib`, `unicodedata`, `contextvars`, `dataclasses`, `argparse`).
- **Complete Feature Implementation (F1 - F10)**:
  - **F1: Claims & Evidence-Based Trust**: Formal `Claim` and `EvidenceRef` data models with `ClaimStore`. Grounded verification via `verify()` and `refute()`. **Peer Agreement Defense**: peer agents agreeing on an unverified claim cannot upgrade trust status without external grounding.
  - **F2: Multi-Agent Lineage Graph**: Directed Acyclic Graph (DAG) for agents, claims, tools, and handoffs implemented purely with Python stdlib dict/set. Kahn's algorithm cycle detection, root-cause `blame()` reports, cross-run `diff()`, and native Mermaid flowchart markdown export.
  - **F3: Handoff Contract**: Structured `HandoffPacket` protocol between collaborating agents with token caps, schema linting (`lint_handoff`), and strict truncation policies. **Critical Constraint**: Constraints are unbreakable and never dropped under any truncation policy.
  - **F4: Action Gate**: Side-effect management (`read`, `write`, `destructive`). Unauthorized destructive tools are blocked in `enforce` mode (or logged in `shadow` mode) unless accompanied by human-in-the-loop confirmation or verified grounding claims. `@guarded` decorator.
  - **F5: Context Pin Re-injection**: Persistent context pins (`PinStore`) that survive context window compaction. Deterministic, idempotent re-injection (`reinject()`) and compaction recovery (`guard_compaction()`).
  - **F6: Compaction Soak Test Harness**: Soak testing harness (`soak()`) exercising multi-turn compactions across `TruncateCompactor`, `LastNCompactor`, and `StubSummarizer`.
  - **F7: Run Fingerprint**: Deterministic canonical hashing (`fingerprint()`) of model parameters, system prompts, tool schemas, and extras with JSON-path selector exclusion (`ignore=["$.params.seed"]`). Distinguishes between structural parameter changes and documentation-only edits.
  - **F8: Drift CI Gate**: Baseline locking (`write_lock_file()`, `agentium lock`) and CI gate verification (`diff_fingerprints()`, `agentium check`). Includes GitHub Composite Action (`.github/actions/agentium-check/action.yml`) with automated PR comments.
  - **F9: Developer Experience & Diagnostics**: Non-intrusive static scanner (`agentium init`) detecting frameworks without executing code, and 9-point system health diagnostics (`agentium doctor`).
  - **F10: Speculative Read-Only Tool Prefetch (Experimental)**: Strictly opt-in acceleration engine using Markov transition prediction and TTL-cached execution, strictly restricted to read-only tools. Includes circuit breaker auto-disable.

### Framework Adapters
- `agentium.adapters.langgraph_adapter`: Integration with LangGraph node execution and checkpoint pin persistence.
- `agentium.adapters.crewai_adapter`: Integration with CrewAI agent task starts, completions, and delegations.
- `agentium.adapters.openai_agents_adapter`: Integration with OpenAI Agents SDK tool execution and ActionGate safety.
- All adapters are lazily loaded: missing dependencies raise clear installation instructions without breaking root package imports.

### Backward Compatibility
- All v1 public classes (`Condenser`, `Optimizer`, `Rearranger`, `Communicator`, `Extractor`, `Translator`, etc.) are preserved in `agentium._v1` and accessible from the root `agentium` namespace with a `DeprecationWarning`.
- Legacy import path `agentium.integrations.gemini` is maintained with a `DeprecationWarning`.
