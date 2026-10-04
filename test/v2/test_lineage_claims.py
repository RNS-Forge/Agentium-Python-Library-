"""Unit tests for F1: Claims, Evidence-Based Trust, and Verifier Registry."""
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

from agentium.lineage.claims import Claim, ClaimStore, EvidenceRef
from agentium.lineage.verify import JsonFieldExtractor, get_verifier, verifier


class TestClaimsAndVerification(unittest.TestCase):
    def test_claim_creation(self):
        store = ClaimStore(run_id="test_run")
        claim = store.add("User account balance is $5,000", source_agent="agent_alpha")
        self.assertEqual(claim.status, "unverified")
        self.assertEqual(claim.source_agent, "agent_alpha")
        self.assertEqual(store.get(claim.id).id, claim.id)

    def test_peer_agreement_defense(self):
        """CRITICAL: Peer agreement cannot upgrade an unverified claim to verified."""
        store = ClaimStore(run_id="test_run")
        claim = store.add("Database migration completed", source_agent="agent_1")
        self.assertEqual(claim.status, "unverified")

        # Agent 2 agrees with Agent 1
        updated = store.record_peer_agreement(claim.id, peer_agent="agent_2")
        self.assertEqual(updated.status, "unverified", "Peer agreement MUST NOT upgrade status to verified!")
        self.assertIn("agent_2", updated.metadata.get("peer_agreements", []))

        # Agent 3 also agrees
        updated2 = store.record_peer_agreement(claim.id, peer_agent="agent_3")
        self.assertEqual(updated2.status, "unverified", "Multiple peer agreements still MUST NOT upgrade status!")

    def test_grounded_verification(self):
        store = ClaimStore(run_id="test_run")
        claim = store.add("Deployment succeeded on port 8080", source_agent="deploy_agent")

        ev = EvidenceRef(
            source_type="tool_call",
            source_id="kubectl_status_12",
            excerpt="Deployment/web: 3/3 pods healthy",
        )
        verified = store.verify(claim.id, verifier_name="k8s_verifier", evidence=ev, confidence=0.98)
        self.assertEqual(verified.status, "verified")
        self.assertEqual(verified.confidence, 0.98)
        self.assertEqual(len(verified.evidence), 1)
        self.assertEqual(verified.verified_by, "k8s_verifier")

    def test_refutation(self):
        store = ClaimStore(run_id="test_run")
        claim = store.add("File exists at /var/log/app.log")
        refuted = store.refute(claim.id, refuter_name="fs_verifier", reason="No such file or directory")
        self.assertEqual(refuted.status, "refuted")
        self.assertEqual(refuted.confidence, 0.0)
        self.assertEqual(refuted.metadata.get("refutation_reason"), "No such file or directory")

    def test_json_field_extractor_verifier(self):
        extractor = JsonFieldExtractor(key_path="data.user.role", expected_value="admin")
        ok, reason, ev = extractor.verify({"data": {"user": {"role": "admin"}}})
        self.assertTrue(ok)
        self.assertIsNone(reason)
        self.assertIsNotNone(ev)
        self.assertIn("admin", ev.excerpt)

        # Mismatch
        ok_bad, reason_bad, _ = extractor.verify({"data": {"user": {"role": "viewer"}}})
        self.assertFalse(ok_bad)
        self.assertIn("mismatch", reason_bad.lower())

    def test_custom_verifier_decorator(self):
        @verifier(name="test_regex_verifier")
        def custom_verifier(claim, text, pattern):
            import re
            matched = bool(re.search(pattern, text))
            if matched:
                return True, None, EvidenceRef("text_scan", "1", "regex match")
            return False, "Pattern not found", None

        fn = get_verifier("test_regex_verifier")
        self.assertIsNotNone(fn)
        ok, _, ev = fn(None, "HTTP 200 OK", r"200 OK")
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
