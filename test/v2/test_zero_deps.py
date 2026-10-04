import os
import sys

# Ensure clean test: run in fresh python execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def test_zero_third_party_dependencies():
    print("Testing that importing agentium core imports zero third-party packages...")

    before_modules = set(sys.modules.keys())

    import agentium

    # Ensure v2 core functions are available
    assert hasattr(agentium, "run")
    assert hasattr(agentium, "tool")
    assert hasattr(agentium, "Event")
    assert hasattr(agentium, "canonical_json")
    assert hasattr(agentium, "estimate_tokens")
    assert agentium.__version__.startswith("2.")

    after_modules = set(sys.modules.keys())
    newly_imported = after_modules - before_modules

    # Filter out agentium's own modules
    newly_imported_external = {m for m in newly_imported if not m.startswith("agentium")}

    # Forbidden third-party modules that must NEVER be imported by agentium core
    forbidden_prefixes = [
        "opentelemetry",
        "langchain",
        "langgraph",
        "crewai",
        "openai",
        "anthropic",
        "redis",
        "numpy",
        "pandas",
        "requests",
        "pydantic",
        "nltk",
        "tiktoken",
        "jinja2",
        "google.generativeai",
        "google.ai",
    ]

    forbidden_found = []
    for mod_name in newly_imported_external:
        for prefix in forbidden_prefixes:
            if mod_name == prefix or mod_name.startswith(f"{prefix}."):
                forbidden_found.append(mod_name)

    assert (
        len(forbidden_found) == 0
    ), f"Zero-dependency violation! Forbidden third-party modules were imported by agentium: {forbidden_found}"

    print(
        f"[PASS] agentium core loaded with ZERO third-party runtime dependencies! ({len(newly_imported_external)} stdlib modules loaded)"
    )


if __name__ == "__main__":
    test_zero_third_party_dependencies()
    print("\nALL ZERO DEPENDENCY TESTS PASSED!")
