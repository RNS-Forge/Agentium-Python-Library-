# Third-Party Libraries Catalog & Licence Audit

> All libraries checked against PyPI metadata on **2026-10-04**.  
> **Core Guarantee**: None of these packages are required by `agentium` core. All are strictly optional extras.

| Extra Name | PyPI Package | Category | Tier | Licence | Requires-Python | PyPI URL | Decision |
|:---|:---|:---|:---:|:---|:---|:---|:---|
| **tenacity** | `tenacity` | Resilience | 1 | Apache-2.0 | `>=3.10` | https://pypi.org/project/tenacity/ | Include |
| **pybreaker** | `pybreaker` | Resilience | 1 | BSD | `>=3.9` | https://pypi.org/project/pybreaker/ | Include |
| **cachetools** | `cachetools` | Cache/Storage | 1 | MIT | `>=3.10` | https://pypi.org/project/cachetools/ | Include |
| **otel** | `opentelemetry-api` | Observability | 1 | Apache-2.0 | `>=3.10` | https://pypi.org/project/opentelemetry-api/ | Include |
| **otelsdk** | `opentelemetry-sdk` | Observability | 1 | Apache-2.0 | `>=3.10` | https://pypi.org/project/opentelemetry-sdk/ | Include |
| **pydantic** | `pydantic` | Validation/Parsing | 1 | MIT | `>=3.9` | https://pypi.org/project/pydantic/ | Include |
| **jsonschema** | `jsonschema` | Validation/Parsing | 1 | MIT | `>=3.10` | https://pypi.org/project/jsonschema/ | Include |
| **jsonrepair** | `json-repair` | Validation/Parsing | 1 | MIT | `>=3.10` | https://pypi.org/project/json-repair/ | Include |
| **jmespath** | `jmespath` | Validation/Parsing | 1 | MIT | `>=3.9` | https://pypi.org/project/jmespath/ | Include |
| **deepdiff** | `deepdiff` | Diff/Compare | 1 | MIT | `>=3.10` | https://pypi.org/project/deepdiff/ | Include |
| **rapidfuzz** | `RapidFuzz` | Diff/Compare | 1 | MIT | `>=3.11` | https://pypi.org/project/RapidFuzz/ | Include |
| **tiktoken** | `tiktoken` | Tokens/LLM | 1 | MIT | `>=3.9` | https://pypi.org/project/tiktoken/ | Include |
| **litellm** | `litellm` | Tokens/LLM | 1 | MIT | `<3.15,>=3.10` | https://pypi.org/project/litellm/ | Include |
| **httpx** | `httpx` | Tokens/LLM | 1 | BSD-3-Clause | `>=3.8` | https://pypi.org/project/httpx/ | Include |
| **langgraph** | `langgraph` | Agent frameworks | 1 | MIT | `>=3.10` | https://pypi.org/project/langgraph/ | Include |
| **langchain** | `langchain` | Agent frameworks | 1 | MIT | `<4.0.0,>=3.10.0` | https://pypi.org/project/langchain/ | Include |
| **crewai** | `crewai` | Agent frameworks | 1 | MIT | `<3.14,>=3.10` | https://pypi.org/project/crewai/ | Include - at risk (<3.14) |
| **openai-agents** | `openai-agents` | Agent frameworks | 1 | MIT | `>=3.10` | https://pypi.org/project/openai-agents/ | Include |
| **mcp** | `mcp` | Agent frameworks | 1 | MIT | `>=3.10` | https://pypi.org/project/mcp/ | Include |
| **pytest** | `pytest` | Testing/Replay | 1 | MIT | `>=3.10` | https://pypi.org/project/pytest/ | Include |
| **detectsecrets** | `detect-secrets` | Security/Privacy | 1 | Apache-2.0 | Not declared | https://pypi.org/project/detect-secrets/ | Include - low priority (stale) |
| **pluggy** | `pluggy` | Utilities | 1 | MIT | `>=3.9` | https://pypi.org/project/pluggy/ | Include |

---

### Excluded Packages

| PyPI Package | Stated Licence | Reason for Exclusion |
|:---|:---|:---|
| `stopit` | Conflict: GPLv3 vs MIT | Licence ambiguity and stale (last release in 2018). Use stdlib `asyncio.timeout` instead. |
| `arize-phoenix` | Elastic-2.0 | Source-available licence (non-OSI). Use the standard OpenTelemetry exporter instead. |
