from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import MappingProxyType

from qseries_v2.observation_intelligence.oi_015_reasoning_input_builder import (
    OracleReasoningInput,
    ReasoningEvidenceItem,
)
from qseries_v2.observation_intelligence.oi_016_evidence_sufficiency_gate import (
    EvidenceSufficiencyGate,
    EvidenceSufficiencyPolicy,
)
from qseries_v2.observation_intelligence.oi_017_observation_change_attribution import (
    ObservationChange,
)
from qseries_v2.observation_intelligence.oi_018_explanation_evidence_package import (
    OI_018_REVISION,
    ExplanationEvidencePackageBuilder,
    verify_explanation_evidence_package,
)

NOW = datetime(2026, 8, 10, 13, 0, tzinfo=timezone.utc)


def input_value():
    item = ReasoningEvidenceItem(
        canonical_observation_id="obs.current",
        canonical_observation_hash="a" * 64,
        provider="Provider",
        adapter_id="adapter.source.a",
        observed_at=NOW,
        freshness_status="fresh",
        subject="TEST",
        observation_type="market_snapshot",
        facts=MappingProxyType({"value": 55}),
    )

    return OracleReasoningInput(
        query_id="query.explain",
        profile_id="profile.market_explanation",
        built_at=NOW,
        evidence_items=(item,),
        required_evidence_count=1,
        satisfied_evidence_count=1,
        missing_evidence_count=0,
        complete_required_evidence=True,
        input_hash="b" * 64,
        predictive=False,
        read_only=True,
    )


def sufficiency():
    return EvidenceSufficiencyGate().evaluate(
        input_value(),
        policy=EvidenceSufficiencyPolicy(
            policy_id="policy.explain",
            minimum_evidence_items=1,
            minimum_distinct_sources=1,
            allow_stale_evidence=False,
        ),
    )


def change():
    return ObservationChange(
        subject="TEST",
        observation_type="market_snapshot",
        value_field="yes_bid",
        prior_observation_id="obs.prior",
        current_observation_id="obs.current",
        prior_value=50.0,
        current_value=55.0,
        absolute_change=5.0,
        relative_change=0.1,
        direction="up",
        change_hash="c" * 64,
    )


class TestOI018(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_evidence_package()
        )

    def test_build(self):
        package = ExplanationEvidencePackageBuilder().build(
            reasoning_input=input_value(),
            sufficiency=sufficiency(),
            changes=(change(),),
            built_at=NOW,
        )

        self.assertTrue(package.sufficient_evidence)
        self.assertEqual(package.evidence_item_count, 1)
        self.assertEqual(package.change_hashes, ("c" * 64,))

    def test_non_causal(self):
        package = ExplanationEvidencePackageBuilder().build(
            reasoning_input=input_value(),
            sufficiency=sufficiency(),
            changes=(change(),),
            built_at=NOW,
        )

        self.assertFalse(package.causal_claim_allowed)
        self.assertFalse(package.predictive)
        self.assertTrue(package.read_only)

    def test_deterministic(self):
        builder = ExplanationEvidencePackageBuilder()
        a = builder.build(
            reasoning_input=input_value(),
            sufficiency=sufficiency(),
            changes=(change(),),
            built_at=NOW,
        )
        b = builder.build(
            reasoning_input=input_value(),
            sufficiency=sufficiency(),
            changes=(change(),),
            built_at=NOW,
        )
        self.assertEqual(a.package_hash, b.package_hash)

    def test_side_effects(self):
        builder = ExplanationEvidencePackageBuilder()
        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.causal_claim_allowed)
        self.assertFalse(builder.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-018 CERTIFICATION TEST")
    print(" EXPLANATION EVIDENCE PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI018
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-018")
    print(f"[PASS] Revision: {OI_018_REVISION}")
    print("[PASS] Reasoning input, evidence sufficiency, and observed changes packaged together")
    print("[PASS] Explanation package preserves evidence lineage and change lineage")
    print("[PASS] Causal claims and predictions remain explicitly disabled")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-018 CERTIFIED")
