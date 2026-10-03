import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.translator import Translator, ToneType

def test_all_tones():
    translator = Translator()
    sample_text = "We can't solve this bad problem. It is a big error and failure."

    print("=" * 60)
    print("TESTING ALL 7 TONES IN AGENTIUM TRANSLATOR (ToneType)")
    print("=" * 60)
    print("Sample Input:", sample_text)
    print("-" * 60)

    for tone in ToneType:
        res = translator.translate(sample_text, target_language="en", tone=tone)
        print(f"[{tone.name}] (value: '{tone.value}')")
        print(f"  -> Transformed Output: {res.get('translated_text')}")
        print(f"  -> Tone Applied:       {res.get('tone_applied')}")
        print()

    detected = translator.detect_tone(sample_text)
    print(f"Automatic Tone Detection on sample: {detected}")
    print("=" * 60)

if __name__ == "__main__":
    test_all_tones()
