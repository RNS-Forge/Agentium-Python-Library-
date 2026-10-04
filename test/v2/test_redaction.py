import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agentium.core.redact import Redactor, redact_payload


def test_copy_on_redact_non_mutation():
    print("Testing copy-on-redact non-mutation...")
    original = {
        "user_email": "alice@example.com",
        "nested": {
            "token": "sk-1234567890abcdef1234567890abcdef",
            "items": ["safe_item", "contact bob@corp.org for help"],
        },
    }

    # Deep snapshot of original
    original_str = str(original)

    redacted, was_modified = redact_payload(original)

    # Assert caller's original object was not mutated
    assert str(original) == original_str
    assert original["user_email"] == "alice@example.com"
    assert was_modified is True

    # Assert copy has redacted values
    assert redacted["user_email"] == "[REDACTED_EMAIL]"
    assert redacted["nested"]["token"] == "[REDACTED_API_KEY]"
    assert "bob@corp.org" not in redacted["nested"]["items"][1]
    print("[PASS] Copy-on-redact non-mutation OK")


def test_api_key_shapes():
    print("Testing common API key shapes...")
    payload = {
        "openai": "sk-abcdef1234567890abcdef1234567890",
        "groq": "gsk_1234567890abcdef1234567890abcdef",
        "openrouter": "sk-or-v1-abcdef1234567890abcdef1234567890",
        "bearer": "Bearer abcdef1234567890abcdef",
    }
    redacted, modified = redact_payload(payload)
    assert modified is True
    assert redacted["openai"] == "[REDACTED_API_KEY]"
    assert redacted["groq"] == "[REDACTED_API_KEY]"
    assert redacted["openrouter"] == "[REDACTED_API_KEY]"
    assert redacted["bearer"] == "Bearer [REDACTED_TOKEN]"
    print("[PASS] All common API key shapes redacted OK")


def test_custom_redaction_pattern():
    print("Testing custom redactor patterns...")
    custom_redactor = Redactor(additional_patterns=[(r"SECRET-[0-9]{4}", "[CONFIDENTIAL]")])
    data = {"secret_code": "Access code is SECRET-9876"}
    res, mod = custom_redactor(data)
    assert mod is True
    assert res["secret_code"] == "Access code is [CONFIDENTIAL]"
    print("[PASS] Custom redactor patterns OK")


if __name__ == "__main__":
    test_copy_on_redact_non_mutation()
    test_api_key_shapes()
    test_custom_redaction_pattern()
    print("\nALL REDACTION TESTS PASSED!")
