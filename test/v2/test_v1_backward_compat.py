import os
import sys
import warnings

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def test_v1_top_level_imports_and_warnings():
    print("Testing v1 top-level imports and deprecation warnings...")
    import agentium

    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")
        Condenser = agentium.Condenser
        Optimizer = agentium.Optimizer
        Communicator = agentium.Communicator
        Agentium = agentium.Agentium

        # Verify classes are functional
        c = Condenser()
        assert c is not None

        # Verify deprecation warnings were emitted
        dep_warnings = [w for w in recorded_warnings if issubclass(w.category, DeprecationWarning)]
        assert len(dep_warnings) >= 4, f"Expected at least 4 DeprecationWarnings, got {len(dep_warnings)}"
        assert any("Condenser" in str(w.message) for w in dep_warnings)
        print("[PASS] Top-level v1 imports with DeprecationWarnings OK")


def test_v1_integrations_shims():
    print("Testing v1 integrations shims...")
    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")
        from agentium.integrations.gemini import GeminiConfig, GeminiIntegration
        from agentium.integrations.crewai import AgentiumCrewTool
        from agentium.integrations.langchain import AgentiumTool
        from agentium.integrations.langgraph import AgentiumNode

        assert GeminiConfig is not None
        assert AgentiumCrewTool is not None
        assert AgentiumTool is not None
        assert AgentiumNode is not None

        dep_warnings = [w for w in recorded_warnings if issubclass(w.category, DeprecationWarning)]
        assert len(dep_warnings) >= 4
        print("[PASS] v1 integrations shims with DeprecationWarnings OK")


if __name__ == "__main__":
    test_v1_top_level_imports_and_warnings()
    test_v1_integrations_shims()
    print("\nALL V1 BACKWARD COMPATIBILITY TESTS PASSED!")
