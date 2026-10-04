import os
import sys
import unicodedata

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agentium.core.hashing import canonical_json, sha256_hex


def test_dict_ordering_and_separators():
    print("Testing dict ordering and compact separators...")
    d1 = {"z": 10, "a": 1, "m": {"nested_b": 2, "nested_a": 1}}
    d2 = {"a": 1, "m": {"nested_a": 1, "nested_b": 2}, "z": 10}

    cj1 = canonical_json(d1)
    cj2 = canonical_json(d2)

    assert cj1 == cj2
    assert " " not in cj1  # compact separators
    assert sha256_hex(d1) == sha256_hex(d2)
    print("[PASS] Dict key ordering & compact separators OK")


def test_unicode_nfc_normalization():
    print("Testing Unicode NFC normalization...")
    # Decomposed vs composed 'é'
    composed = "\u00e9"  # e with acute
    decomposed = "e\u0301"  # 'e' + combining acute accent
    assert composed != decomposed  # raw Python strings differ

    cj_comp = canonical_json({"accent": composed})
    cj_decomp = canonical_json({"accent": decomposed})

    assert cj_comp == cj_decomp
    assert sha256_hex({"accent": composed}) == sha256_hex({"accent": decomposed})
    print("[PASS] Unicode NFC normalization OK")


def test_float_integer_normalization():
    print("Testing float integer normalization (1.0 vs 1)...")
    d_float = {"int_val": 1.0, "sub": [2.0, 3.5]}
    d_int = {"int_val": 1, "sub": [2, 3.5]}

    cj_float = canonical_json(d_float)
    cj_int = canonical_json(d_int)

    assert cj_float == cj_int
    assert sha256_hex(d_float) == sha256_hex(d_int)
    print("[PASS] Integer-valued float normalization OK")


def test_booleans_not_coerced():
    print("Testing booleans are preserved and not coerced to 1/0...")
    d_bool = {"active": True, "failed": False}
    d_num = {"active": 1, "failed": 0}

    cj_bool = canonical_json(d_bool)
    cj_num = canonical_json(d_num)

    assert cj_bool != cj_num
    assert '"active":true' in cj_bool
    assert '"failed":false' in cj_bool
    print("[PASS] Booleans preserved strictly OK")


def test_nan_infinity_rejected():
    print("Testing NaN and Infinity rejection with ValueError...")
    for bad_val in [float("nan"), float("inf"), float("-inf")]:
        try:
            canonical_json({"bad": bad_val})
            assert False, f"Expected ValueError for {bad_val}"
        except ValueError:
            pass
    print("[PASS] NaN/Infinity rejected strictly OK")


if __name__ == "__main__":
    test_dict_ordering_and_separators()
    test_unicode_nfc_normalization()
    test_float_integer_normalization()
    test_booleans_not_coerced()
    test_nan_infinity_rejected()
    print("\nALL CANONICAL HASHING TESTS PASSED!")
