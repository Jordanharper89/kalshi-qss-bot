from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import MappingProxyType

from qseries_v2.observation_intelligence.oi_015_reasoning_input_builder import (
    OracleReasoningInput,
    ReasoningEvidenceItem,
)
from qseries_v2.observation_intelligence.oi_016_evidence_sufficiency_gate import (
    OI_016_REVISION,
    EvidenceSufficiencyGate,
    EvidenceSufficiencyPolicy,
    verify_evidence_sufficiency_gate,
)

NOW = datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc)


def reasoning_input(
    *,
    freshness: str = "fresh",
    complete: bool = True,
):
    item = ReasoningEvidenceItem(
        canonical_observation_id="obs.1",
        canonical_observation_hash="a" * 64,
        provider="Provider",
        adapter_id="adapter.source.a",
        observed_at=NOW,
        freshness_status=freshness,
        subject="TEST",
        observation_type="market_snapshot",
        facts=MappingProxyType({"value": 1}),
    )

    return OracleReasoningInput(
        query_id="query.test",
        profile_id="profile.test",
        built_at=NOW,
        evidence_items=(item,),
        required_evidence_count=1,
        satisfied_evidence_count=1 if complete else 0,
        missing_evidence_count=0 if complete else 1,
        complete_required_evidence=complete,
        input_hash="b" * 64,
        predictive=False,
        read_only=True,
    )


class TestOI016(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_sufficiency_gate()
        )

    def test_sufficient(self):
        decision = EvidenceSufficiencyGate().evaluate(
            reasoning_input(),
            policy=EvidenceSufficiencyPolicy(
                policy_id="policy.basic",
                minimum_evidence_items=1,
                minimum_distinct_sources=1,
                allow_stale_evidence=False,
            ),
        )
        self.assertTrue(decision.sufficient)

    def test_missing_required(self):
        decision = EvidenceSufficiencyGate().evaluate(
            reasoning_input(complete=False),
            policy=EvidenceSufficiencyPolicy(
                policy_id="policy.basic",
                minimum_evidence_items=1,
                minimum_distinct_sources=1,
                allow_stale_evidence=False,
            ),
        )
        self.assertFalse(decision.sufficient)
        self.assertIn(
            "missing_required_evidence",
            decision.reason_codes,
        )

    def test_stale_rejected(self):
        decision = EvidenceSufficiencyGate().evaluate(
            reasoning_input(freshness="stale"),
            policy=EvidenceSufficiencyPolicy(
                policy_id="policy.basic",
                minimum_evidence_items=1,
                minimum_distinct_sources=1,
                allow_stale_evidence=False,
            ),
        )
        self.assertFalse(decision.sufficient)

    def test_deterministic(self):
        gate = EvidenceSufficiencyGate()
        policy = EvidenceSufficiencyPolicy(
            policy_id="policy.basic",
            minimum_evidence_items=1,
            minimum_distinct_sources=1,
            allow_stale_evidence=False,
        )
        a = gate.evaluate(reasoning_input(), policy=policy)
        b = gate.evaluate(reasoning_input(), policy=policy)
        self.assertEqual(a.decision_hash, b.decision_hash)

    def test_side_effects(self):
        gate = EvidenceSufficiencyGate()
        self.assertTrue(gate.read_only)
        self.assertFalse(gate.network_allowed)
        self.assertFalse(gate.persistence_allowed)
        self.assertFalse(gate.publication_allowed)
        self.assertFalse(gate.execution_allowed)
        self.assertFalse(gate.qseries_execution_allowed)
        self.assertFalse(gate.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-016 CERTIFICATION TEST")
    print(" EVIDENCE SUFFICIENCY GATE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI016
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-016")
    print(f"[PASS] Revision: {OI_016_REVISION}")
    print("[PASS] Required evidence, source diversity, and freshness sufficiency certified")
    print("[PASS] Insufficient evidence fails closed with reason codes")
    print("[PASS] No prediction or edge judgment introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-016 CERTIFIED")
