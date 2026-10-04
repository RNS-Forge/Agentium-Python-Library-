# Agentium v2 — Architectural Decisions Log

This document records all non-obvious design decisions, rationales, and breaking change considerations in accordance with the Agentium v2 specification.

---

### [2026-10-04] D1: Python 3.11+ Requirement & Zero Runtime Dependencies
- **Context**: Python 3.10 reaches End-Of-Life in October 2026. Python 3.11 introduces `tomllib` in the standard library.
- **Decision**: Set `requires-python = ">=3.11"` and mandate 0 third-party runtime dependencies for `agentium` core.
- **Rationale**: Eliminating all runtime dependencies ensures Agentium cannot break downstream dependency trees, cannot cause supply chain vulnerabilities, and works completely offline out-of-the-box. Any framework integration is an optional extra.
- **Migration Note**: Users on Python 3.10 must pin `agentium<2.0.0`.

---

### [2026-10-04] D2: Preservation of v1 Architecture Under `_v1/`
- **Context**: Agentium v1.x provided text processing helpers (Condenser, Optimizer, Rearranger, Communicator, etc.) and direct framework integrations in `agentium.integrations.*`.
- **Decision**: Relocate the v1 codebase intact under `src/agentium/_v1/`. Expose compatibility shims at `agentium.integrations.*` and top-level `agentium` that emit `DeprecationWarning` while preserving full behavioral backward compatibility.
- **Namespace Rule**: `agentium.integrations.*` is reserved strictly for v1 deprecated shims. All new v2 adapters reside in `agentium.adapters.*`.

---

### [2026-10-04] D3: Canonical Hashing and Float Normalization
- **Context**: Cross-platform determinism requires identical hashing across Linux, macOS, and Windows.
- **Decision**: Implement `canonical_json` with Unicode NFC normalization, sorted keys, compact separators `(",", ":")`, and normalization of integer-valued floats (e.g. `1.0` -> `1`). `NaN` and `Infinity` are rejected explicitly with `ValueError`.
- **Rationale**: In dynamic environments and tool schemas, numbers like `1` and `1.0` frequently interchange in JSON serialization. Treating them identically prevents false positive drift detections in F7/F8. Note: this is an Agentium canonicalization convention and not RFC 8785 (JCS).

---

### [2026-10-04] D4: Multi-Process Event Log Isolation (`<run_id>.<pid>.jsonl`)
- **Context**: Concurrent multi-process execution (e.g. workers using `multiprocessing`) appending to a single JSONL file causes write interleaving and file lock contention, particularly on Windows.
- **Decision**: Event logging writes to `.agentium/events/<run_id>.<pid>.jsonl`. The event reader discovers all files matching `<run_id>.*.jsonl` and merges events deterministically by timestamp (`ts`) and monotonic `event_id`.
- **Rationale**: Guarantees zero file corruption without requiring cross-process mutexes or IPC daemons.

---

### [2026-10-04] D5: Copy-on-Redact Policy
- **Context**: In-flight payload logging must not accidentally mutate live dictionaries or objects passed by the user's agent application.
- **Decision**: All redactors perform deep copies of dictionaries and lists before applying regex masking, leaving caller arguments completely untouched.

---

### [2026-10-04] D6: Peer-Agreement Defense in Claims Architecture
- **Context**: In multi-agent pipelines, Agent B frequently consumes and repeats unverified statements proposed by Agent A.
- **Decision**: Recording peer agreement (`record_peer_agreement()`) updates provenance metadata but CANNOT change a claim's status from `unverified` to `verified`.
- **Rationale**: Multiple AI models hallucinating or echoing the same ungrounded statement does not make it true. Status can only be upgraded to `verified` via external grounding evidence (database record, tool output, HTTP response).

---

### [2026-10-04] D7: Zero-Dependency DAG for Multi-Agent Lineage Graph
- **Context**: Graph representation of multi-agent interactions usually relies on `networkx`.
- **Decision**: Implement `LineageGraph` using pure Python standard library data structures (`dict`, `set`, `deque`) and Kahn's algorithm for topological sorting and cycle detection.
- **Rationale**: Preserves the Zero Core Runtime Dependency Pledge while providing instant cycle detection, Mermaid flowchart generation, and root-cause blame reports.

---

### [2026-10-04] D8: Non-Droppable Constraints Invariant in Handoff Truncation
- **Context**: When handoff packets between agents exceed token limits, truncation policies drop context or unverified claims.
- **Decision**: Operational constraints in `HandoffPacket.constraints` are strictly inviolable and can NEVER be dropped under any policy. If constraints alone exceed `max_tokens`, an explicit `HandoffOverflowError` is raised.
- **Rationale**: Security boundaries, legal disclaimers, and user constraints must never be silently discarded to make room for conversational text.

---

### [2026-10-04] D9: Static Analysis for Project Initialization (`agentium init`)
- **Context**: Automatic framework detection could execute `import` statements or run project modules, potentially triggering side-effects.
- **Decision**: `agentium init` inspects `pyproject.toml`, `requirements.txt`, and file contents using regex and string matching only. It never calls `import` or executes user code.
- **Rationale**: Safe to run in any untrusted repository or CI environment without execution risks.

---

### [2026-10-04] D10: Speculative Prefetch Read-Only Invariant and Circuit Breakers
- **Context**: Speculative execution could accidentally perform destructive operations (e.g., deleting database rows or sending duplicate emails).
- **Decision**: Speculative prefetch (`PrefetchManager`) strictly enforces:
  1. Only tools decorated with `@tool(effect="read")` can be prefetched.
  2. Opt-in only via config or `AGENTIUM_EXPERIMENTAL_PREFETCH=1`.
  3. Automatic circuit breaker disabling the feature if wasted calls exceed 5 or hit rate drops below 30%.
- **Rationale**: Prevents accidental mutations and stops wasted API spend automatically.
