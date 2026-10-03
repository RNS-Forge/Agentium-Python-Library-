import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.translator import Translator, ToneType

def test_translator():
    print("=== Testing Translator ===")
    translator = Translator()
    
    # 1. Translation with tone adaptation (Professional)
    sample_text = "This is a very good product, but we have a small problem with delivery."
    res_prof = translator.translate(sample_text, target_language="es", tone=ToneType.PROFESSIONAL)
    print("Professional Translation Result:", res_prof)
    assert "translated_text" in res_prof, "Expected translated_text in result"
    assert res_prof.get("skipped") is False, "Translation was skipped"
    
    # 2. Translation with Friendly tone
    res_friend = translator.translate(sample_text, target_language="fr", tone=ToneType.FRIENDLY)
    print("Friendly Translation Result:", res_friend)
    assert "translated_text" in res_friend, "Expected translated_text in result"

    print("Result: PASS\n")

if __name__ == "__main__":
    test_translator()
