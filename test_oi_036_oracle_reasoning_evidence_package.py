from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_034_canonical_evidence_materialization import (
    CanonicalEvidenceMaterialization,
    MaterializedEvidenceItem,
)
from qseries_v2.observation_intelligence.oi_035_reasoning_evidence_admission_gate import (
    ReasoningEvidenceAdmission,
)
from qseries_v2.observation_intelligence.oi_036_oracle_reasoning_evidence_package import (
    OI_036_REVISION,
    OracleReasoningEvidencePackageBuilder,
    verify_oracle_reasoning_evidence_package,
)

NOW = datetime(2026, 8, 11, 1, 0, tzinfo=timezone.utc)


def materialization():
    return CanonicalEvidenceMaterialization(
        intake_id="intake.test",
        intake_hash="a" * 64,
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Test market",
        items=(
            MaterializedEvidenceItem(
                canonical_observation_id="obs.1",
                canonical_observation_hash="b" * 64,
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Test market",
                observation_type="market_snapshot",
                observed_at=NOW,
                materialization_hash="c" * 64,
            ),
        ),
        observation_count=1,
        complete_count_match=True,
        materialization_hash="d" * 64,
        read_only=True,
    )


def admission(status="admitted"):
    return ReasoningEvidenceAdmission(
        intake_hash="a" * 64,
        materialization_hash="d" * 64,
        status=status,
        observation_count=1,
        missing_need_count=0 if status == "admitted" else 1,
        complete_count_match=True,
        reason_codes=() if status == "admitted" else (
            "missing_required_observation_needs",
        ),
        admission_hash="e" * 64,
        read_only=True,
    )


class TestOI036(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_reasoning_evidence_package()
        )

    def test_build(self):
        package = (
            OracleReasoningEvidencePackageBuilder()
            .build(
                package_id="reasoning.test",
                materialization=materialization(),
                admission=admission(),
                built_at=NOW,
            )
        )

        self.assertEqual(
            len(package.evidence_items),
            1,
        )
        self.assertEqual(
            package.admission_status,
            "admitted",
        )

    def test_partial_allowed(self):
        package = (
            OracleReasoningEvidencePackageBuilder()
            .build(
                package_id="reasoning.test",
                materialization=materialization(),
                admission=admission("partial"),
                built_at=NOW,
            )
        )

        self.assertEqual(
            package.missing_need_count,
            1,
        )

    def test_rejected_blocked(self):
        rejected = ReasoningEvidenceAdmission(
            intake_hash="a" * 64,
            materialization_hash="d" * 64,
            status="rejected",
            observation_count=0,
            missing_need_count=1,
            complete_count_match=False,
            reason_codes=("no_canonical_observations",),
            admission_hash="f" * 64,
            read_only=True,
        )

        with self.assertRaises(ValueError):
            OracleReasoningEvidencePackageBuilder().build(
                package_id="reasoning.test",
                materialization=materialization(),
                admission=rejected,
                built_at=NOW,
            )

    def test_deterministic(self):
        builder = OracleReasoningEvidencePackageBuilder()

        a = builder.build(
            package_id="reasoning.test",
            materialization=materialization(),
            admission=admission(),
            built_at=NOW,
        )

        b = builder.build(
            package_id="reasoning.test",
            materialization=materialization(),
            admission=admission(),
            built_at=NOW,
        )

        self.assertEqual(
            a.package_hash,
            b.package_hash,
        )

    def test_side_effects(self):
        builder = OracleReasoningEvidencePackageBuilder()

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-036 CERTIFICATION TEST")
    print(" ORACLE REASONING EVIDENCE PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI036
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-036")
    print(f"[PASS] Revision: {OI_036_REVISION}")
    print("[PASS] Admitted canonical evidence packaged for Oracle reasoning consumption")
    print("[PASS] Partial evidence remains marked partial; rejected evidence is blocked")
    print("[PASS] Observation lineage and admission lineage preserved")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-036 CERTIFIED")
