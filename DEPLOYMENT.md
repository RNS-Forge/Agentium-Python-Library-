# Agentium v2.0.3 — Enterprise Deployment & Distribution Guide

Agentium is a zero-core-dependency context and trust integrity library engineered for multi-agent and long-running autonomous AI systems. This guide provides comprehensive, production-grade instructions for building, validating, containerizing, and deploying Agentium across development, staging, CI/CD pipelines, PyPI, and air-gapped enterprise environments.

---

## 1. Architecture & Zero-Dependency Guarantee

- **Core Runtime**: Requires Python **3.11+ Standard Library exclusively**.
- **Cold Start Overhead**: < 1.2 ms (zero heavy framework imports at startup).
- **Core Dependencies**: Zero third-party packages in core runtime (`tomllib`, `hashlib`, `contextvars`, `dataclasses`, `unicodedata`, `argparse`).
- **Isolation**: Framework adapters (LangGraph, CrewAI, OpenAI Agents SDK, LiteLLM, Pydantic, Tenacity, OpenTelemetry) load on-demand only when invoked by the user or application.

```
+-------------------------------------------------------------------+
|                        Your Agent Application                     |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                      Agentium v2 Public APIs                       |
|   - Context Pins (F5)          - Evidence Claims & Defense (F1)   |
|   - Action Gate (F4)           - Provenance Lineage Graph (F2)    |
|   - Handoff Contracts (F3)     - Run Fingerprints & Drift (F7,F8) |
|   - Speculative Prefetch (F10) - System Health & Diagnostics (F9) |
|   - Universal Wrap Hub (M5b)   - Tier-1 Integration Recipes (20)  |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                      Agentium v2 Core Engine                      |
|       (Events, Redaction, Hashing, Tokens, Config, RunScopes)     |
|           [Zero Third-Party Dependencies - Stdlib Only]           |
+-------------------------------------------------------------------+
         |                        |                        |
         v (lazy / optional)      v (lazy / optional)      v (backward compat)
+------------------+    +------------------+    +-------------------+
| Framework Adapters|    | Tier-1 Adapters  |    | Agentium v1 Shims |
| (LangGraph,      |    | (Pydantic,       |    | (Condenser,       |
|  CrewAI,         |    |  Tenacity,       |    |  Optimizer,       |
|  OpenAI Agents)  |    |  Cachetools)     |    |  Rearranger)      |
+------------------+    +------------------+    +-------------------+
```

---

## 2. Installation Targets & Packaging Options

### 2.1 Standard Core Installation (Zero Third-Party Dependencies)

```bash
pip install agentium
```

### 2.2 Framework & Ecosystem Extras

Install optional dependencies on-demand based on your deployment tier:

```bash
# Observability & Tracing
pip install "agentium[otel]"          # OpenTelemetry API & SDK

# Resilience & Tool Caching
pip install "agentium[tenacity]"      # Retry logic
pip install "agentium[cachetools]"    # In-memory TTL/LRU caches
pip install "agentium[pybreaker]"     # Circuit breaker protection

# Schema Validation & Diffs
pip install "agentium[pydantic]"      # Pydantic v2 validation
pip install "agentium[jsonschema]"    # Draft-7 JSON schema validator
pip install "agentium[rapidfuzz]"     # High-speed string distance & deduplication

# Framework Adapters
pip install "agentium[langgraph]"     # LangGraph workflow nodes & checkpointers
pip install "agentium[crewai]"        # CrewAI tool & agent wrappers
pip install "agentium[openai-agents]" # OpenAI Agents SDK integration
pip install "agentium[mcp]"           # Model Context Protocol tools

# Full Developer Suite
pip install "agentium[dev]"           # pytest, ruff, mypy, hypothesis
```

---

## 3. Package Verification & Build Pipeline

Agentium includes a two-tiered build validation process adhering to PEP 517 and PEP 660 standards.

### 3.1 Pre-Deployment Verification

Execute the test suites to ensure 100% test coverage and verify zero external dependencies:

```bash
# 1. Verify Zero Core Dependencies
python test/v2/test_zero_deps.py

# 2. Run Agentium v2 Master Test Suite (27 suites)
python test/v2/run_all_v2_tests.py

# 3. Run Agentium v1 Backward-Compatibility Test Suite (14 suites)
python test/v1/run_all_tests.py
```

### 3.2 Building Distribution Packages

```bash
# Clean previous build artifacts
python -c "import shutil, os; [shutil.rmtree(p, ignore_errors=True) for p in ('build', 'dist', 'src/agentium.egg-info')]"

# Build standard wheel and source tarball
python -m build

# Validate package metadata with Twine
python -m twine check dist/*
```

**Expected Artifacts:**
- `dist/agentium-2.0.0-py3-none-any.whl` (Pure Python wheel, compatible with Python 3.11+)
- `dist/agentium-2.0.0.tar.gz` (Source distribution)

---

## 4. PyPI Publishing Workflow

### 4.1 Deployment to TestPyPI (Staging Verification)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation in an isolated virtual environment
python -m venv test_env
source test_env/bin/activate  # Or test_env\Scripts\activate on Windows
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentium==2.0.0
python -c "import agentium; print('Installed Agentium version:', agentium.__version__)"
```

### 4.2 Deployment to Production PyPI

Using secure PyPI API tokens:

```bash
# Set PyPI credentials
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-your-production-token"

# On Windows PowerShell:
# $env:TWINE_USERNAME="__token__"
# $env:TWINE_PASSWORD="pypi-your-production-token"

# Upload to production PyPI
python -m twine upload dist/*
```

---

## 5. Automated CI/CD Deployment with GitHub Actions

The repository includes a production-grade GitHub Actions workflow at [`.github/workflows/publish.yml`](file:///.github/workflows/publish.yml):

1. **Trigger Options**:
   - **Tag Release**: Automatically fires when a GitHub release is published.
   - **Manual Dispatch**: Can be triggered manually from GitHub Actions UI targeting `testpypi` or `pypi`.
2. **Quality Gates**:
   - Executes matrix tests across Python 3.11, 3.12, and 3.13.
   - Strictly enforces zero runtime dependencies test.
   - Builds distribution wheels and tarballs with `python -m build`.
   - Validates distribution integrity via `twine check`.
   - Publishes securely via OpenID Connect (OIDC) or repository secrets (`PYPI_API_TOKEN` / `TESTPYPI_API_TOKEN`).

---

## 6. Containerized & Docker Deployments

### 6.1 Minimal Production Dockerfile

```dockerfile
FROM python:3.12-slim-bookworm AS base

# Security: Non-root execution
RUN groupadd -g 1001 appuser && \
    useradd -u 1001 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Install Agentium Core (Zero dependencies)
RUN pip install --no-cache-dir agentium==2.0.2

# Copy application source code
COPY --chown=appuser:appuser . /app

USER appuser

# Healthcheck using agentium doctor
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -m agentium doctor --strict || exit 1

ENTRYPOINT ["python", "app.py"]
```

---

## 7. Operational Health Checks & Telemetry

### 7.1 Diagnostic Health Check

Run Agentium's built-in 9-point static diagnostic scanner:

```bash
# Standard health check
agentium doctor

# Strict CI mode (fails on warnings)
agentium doctor --strict

# Machine-readable JSON output for monitoring systems
agentium doctor --json
```

### 7.2 OpenTelemetry Integration

Export event streams to Datadog, Honeycomb, Dynatrace, or Jaeger:

```python
import agentium
from agentium.core.otel import OtelExporter

# Lazy-loaded OTEL exporter
exporter = OtelExporter(service_name="payment_agent_cluster")
with agentium.run("run_production_9901") as r:
    # Agent activities recorded automatically to OpenTelemetry spans
    pass
```

---

## 8. Enterprise Pre-Flight Checklist

- [x] Python 3.11+ runtime verified.
- [x] Core package verified with **zero external runtime dependencies**.
- [x] All 27 Agentium v2 master feature test suites passing.
- [x] All 14 legacy v1 backward-compatibility test suites passing.
- [x] Built wheel and sdist verified with `twine check` (100% valid).
- [x] Documentation compiled to publication-quality PDF and Markdown in `Document/`.
- [x] Secret redaction patterns verified against API tokens (`sk-`, `ghp_`, `xoxb-`).
- [x] Git release tag (`v2.0.0`) signed and pushed to upstream remote.