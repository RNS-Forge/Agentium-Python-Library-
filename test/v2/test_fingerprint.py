"""Unit tests for F7: Run Fingerprint (agentium.fingerprint)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentium.fingerprint.fp import Fingerprint, fingerprint


class TestFingerprint(unittest.TestCase):
    def test_deterministic_identical_inputs(self):
        fp1 = fingerprint(
            model="gpt-4o",
            params={"temperature": 0.2, "seed": 42},
            system_prompt="You are a helpful assistant.",
            tools=[
                {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                }
            ],
        )
        fp2 = fingerprint(
            model="gpt-4o",
            params={"seed": 42, "temperature": 0.2},  # reversed key order
            system_prompt="You are a helpful assistant.",
            tools=[
                {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                }
            ],
        )
        self.assertEqual(fp1.model_and_params, fp2.model_and_params)
        self.assertEqual(fp1.system_prompt, fp2.system_prompt)
        self.assertEqual(fp1.tools_full, fp2.tools_full)
        self.assertEqual(fp1.tools_structure, fp2.tools_structure)
        self.assertEqual(fp1.combined, fp2.combined)

    def test_description_only_change_affects_full_not_structure(self):
        tools_v1 = [
            {
                "name": "search",
                "description": "Search Google for info",
                "parameters": {"type": "object", "properties": {"q": {"type": "string"}}},
            }
        ]
        tools_v2 = [
            {
                "name": "search",
                "description": "Search Bing for info (updated docstring)",
                "parameters": {"type": "object", "properties": {"q": {"type": "string"}}},
            }
        ]

        fp1 = fingerprint(model="claude-3-5-sonnet", tools=tools_v1)
        fp2 = fingerprint(model="claude-3-5-sonnet", tools=tools_v2)

        # tools_full should differ because description changed
        self.assertNotEqual(fp1.tools_full, fp2.tools_full)
        # tools_structure should be IDENTICAL because names, types, and schema shape are identical
        self.assertEqual(fp1.tools_structure, fp2.tools_structure)

    def test_structural_tool_change_affects_both(self):
        tools_v1 = [
            {
                "name": "calc",
                "parameters": {"type": "object", "properties": {"x": {"type": "number"}}},
            }
        ]
        tools_v2 = [
            {
                "name": "calc",
                "parameters": {
                    "type": "object",
                    "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
                },
            }
        ]

        fp1 = fingerprint(model="m", tools=tools_v1)
        fp2 = fingerprint(model="m", tools=tools_v2)

        self.assertNotEqual(fp1.tools_structure, fp2.tools_structure)
        self.assertNotEqual(fp1.tools_full, fp2.tools_full)

    def test_ignore_selectors(self):
        # Ignore seed parameter
        fp1 = fingerprint(
            model="gpt-4o",
            params={"temperature": 0.7, "seed": 100},
            ignore=["$.params.seed"],
        )
        fp2 = fingerprint(
            model="gpt-4o",
            params={"temperature": 0.7, "seed": 999},
            ignore=["$.params.seed"],
        )
        self.assertEqual(fp1.model_and_params, fp2.model_and_params)
        self.assertEqual(fp1.combined, fp2.combined)

        # Without ignore, they must differ
        fp3 = fingerprint(model="gpt-4o", params={"temperature": 0.7, "seed": 999})
        fp4 = fingerprint(model="gpt-4o", params={"temperature": 0.7, "seed": 100})
        self.assertNotEqual(fp3.model_and_params, fp4.model_and_params)

    def test_unicode_and_whitespace_normalization(self):
        # NFC vs NFD
        # 'e' with acute accent: é can be \u00e9 (NFC) or e + \u0301 (NFD)
        nfc_prompt = "Caf\u00e9 menu"
        nfd_prompt = "Cafe\u0301 menu"

        fp1 = fingerprint(model="m", system_prompt=nfc_prompt)
        fp2 = fingerprint(model="m", system_prompt=nfd_prompt)
        self.assertEqual(fp1.system_prompt, fp2.system_prompt)

    def test_extras_component(self):
        fp1 = fingerprint(model="m", extras={"rag_index_version": "v1.2"})
        fp2 = fingerprint(model="m", extras={"rag_index_version": "v1.3"})
        self.assertNotEqual(fp1.extras, fp2.extras)
        self.assertNotEqual(fp1.combined, fp2.combined)


if __name__ == "__main__":
    unittest.main()
