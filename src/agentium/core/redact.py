from __future__ import annotations

import copy
import re
from typing import Any, Callable, Dict, List, Pattern, Tuple, Union

DEFAULT_PATTERNS: List[Tuple[Pattern[str], str]] = [
    # API key patterns (OpenAI, Groq, OpenRouter, Anthropic, generic tokens)
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"sk-or-v1-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"gsk_[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"ant-api-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{16,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED_EMAIL]"),
]


class Redactor:
    """Copy-on-redact engine that masks sensitive secrets and personal info
    without ever mutating the original input object."""

    def __init__(self, additional_patterns: List[Tuple[Union[Pattern[str], str], str]] | None = None) -> None:
        self.patterns: List[Tuple[Pattern[str], str]] = list(DEFAULT_PATTERNS)
        if additional_patterns:
            for pat, repl in additional_patterns:
                compiled = pat if isinstance(pat, Pattern) else re.compile(pat)
                self.patterns.append((compiled, repl))

    def _redact_string(self, text: str) -> Tuple[str, bool]:
        modified = False
        result = text
        for pattern, replacement in self.patterns:
            new_text, count = pattern.subn(replacement, result)
            if count > 0:
                modified = True
                result = new_text
        return result, modified

    def _redact_recursive(self, item: Any) -> Tuple[Any, bool]:
        if isinstance(item, str):
            return self._redact_string(item)
        elif isinstance(item, dict):
            new_dict = {}
            any_modified = False
            for k, v in item.items():
                k_redacted, k_mod = self._redact_string(str(k))
                v_redacted, v_mod = self._redact_recursive(v)
                new_dict[k_redacted] = v_redacted
                if k_mod or v_mod:
                    any_modified = True
            return new_dict, any_modified
        elif isinstance(item, list):
            new_list = []
            any_modified = False
            for elem in item:
                elem_redacted, elem_mod = self._redact_recursive(elem)
                new_list.append(elem_redacted)
                if elem_mod:
                    any_modified = True
            return new_list, any_modified
        elif isinstance(item, tuple):
            redacted_elems = []
            any_modified = False
            for elem in item:
                elem_redacted, elem_mod = self._redact_recursive(elem)
                redacted_elems.append(elem_redacted)
                if elem_mod:
                    any_modified = True
            return tuple(redacted_elems), any_modified
        elif isinstance(item, set):
            new_set = set()
            any_modified = False
            for elem in item:
                elem_redacted, elem_mod = self._redact_recursive(elem)
                new_set.add(elem_redacted)
                if elem_mod:
                    any_modified = True
            return new_set, any_modified
        return item, False

    def __call__(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """Perform copy-on-redact. Returns (new_payload, was_redacted)."""
        copied = copy.deepcopy(payload)
        redacted_payload, was_modified = self._redact_recursive(copied)
        return (redacted_payload if isinstance(redacted_payload, dict) else {"data": redacted_payload}), was_modified


_global_redactor = Redactor()


def get_default_redactor() -> Redactor:
    return _global_redactor


def redact_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    return _global_redactor(payload)
