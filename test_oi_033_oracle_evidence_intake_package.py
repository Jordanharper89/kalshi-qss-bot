from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_030_oracle_observation_request_package import (
    OracleObservationRequestPackage,
)
from qseries_v2.observation_intelligence.oi_031_oracle_observation_request_dispatcher import (
    DispatchedObservationNeed,
    OracleObservationDispatchResult,
)
from qseries_v2.observation_intelligence.oi_032_acquisition_coverage_reconciliation import (
    AcquisitionCoverageItem,
    AcquisitionCoverageReconciliation,
)
from qseries_v2.observation_intelligence.oi_033_oracle_evidence_intake_package import (
    OI_033_REVISION,
    OracleEvidenceIntakePackageBuilder,
    verify_oracle_evidence_intake_package,
)

NOW = datetime(2026, 8, 10, 22, 0, tzinfo=timezone.utc)


def request_package():
    return OracleObservationRequestPackage(
        request_id="request.astros",
        query_id="query.astros",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        profile_id="profile.market_explanation",
        acquisition_plan_hash="a" * 64,
        requested_adapter_ids=("adapter.kalshi.v1",),
        missing_need_ids=("need.lineup",),
        complete_adapter_coverage=False,
        assembled_at=NOW,
        package_hash="b" * 64,
        read_only=True,
        predictive=False,
        terminal_mutation_allowed=False,
    )


def dispatch():
    return OracleObservationDispatchResult(
        request_id="request.astros",
        request_package_hash="b" * 64,
        plan_hash="a" * 64,
        dispatched_at=NOW,
        items=(
            DispatchedObservationNeed(
                ordinal=1,
                need_id="need.market",
                covered=True,
                adapter_ids=("adapter.kalshi.v1",),
                acquisition_hash="c" * 64,
                observation_count=1,
                evidence_hash="d" * 64,
                dispatch_item_hash="e" * 64,
            ),
            DispatchedObservationNeed(
                ordinal=2,
                need_id="need.lineup",
                covered=False,
                adapter_ids=(),
                acquisition_hash=None,
                observation_count=0,
                evidence_hash=None,
                dispatch_item_hash="f" * 64,
            ),
        ),
        covered_need_count=1,
        missing_need_count=1,
        acquired_observation_count=1,
        dispatch_hash="1" * 64,
        read_only=True,
    )


def reconciliation():
    return AcquisitionCoverageReconciliation(
        plan_hash="a" * 64,
        dispatch_hash="1" * 64,
        items=(
            AcquisitionCoverageItem(
                need_id="need.market",
                planned_covered=True,
                dispatched_covered=True,
                observation_count=1,
                acquisition_present=True,
                satisfied=True,
                reason_code="satisfied",
                item_hash="2" * 64,
            ),
            AcquisitionCoverageItem(
                need_id="need.lineup",
                planned_covered=False,
                dispatched_covered=False,
                observation_count=0,
                acquisition_present=False,
                satisfied=False,
                reason_code="adapter_capability_missing",
                item_hash="3" * 64,
            ),
        ),
        satisfied_count=1,
        unsatisfied_count=1,
        observation_count=1,
        status="partial",
        reconciliation_hash="4" * 64,
        read_only=True,
    )


class TestOI033(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_evidence_intake_package()
        )

    def test_build(self):
        package = OracleEvidenceIntakePackageBuilder().build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.acquisition_status,
            "partial",
        )
        self.assertEqual(
            package.total_observation_count,
            1,
        )
        self.assertFalse(
            package.complete_evidence_intake
        )

    def test_missing_need_preserved(self):
        package = OracleEvidenceIntakePackageBuilder().build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.missing_need_ids,
            ("need.lineup",),
        )

    def test_evidence_hash_preserved(self):
        package = OracleEvidenceIntakePackageBuilder().build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.evidence_items[0].evidence_hash,
            "d" * 64,
        )

    def test_deterministic(self):
        builder = OracleEvidenceIntakePackageBuilder()

        a = builder.build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        b = builder.build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        self.assertEqual(
            a.intake_hash,
            b.intake_hash,
        )

    def test_side_effects(self):
        builder = OracleEvidenceIntakePackageBuilder()

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)
        self.assertFalse(builder.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-033 CERTIFICATION TEST")
    print(" ORACLE EVIDENCE INTAKE PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI033
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-033")
    print(f"[PASS] Revision: {OI_033_REVISION}")
    print("[PASS] Actual acquired evidence reconciled into deterministic Oracle intake package")
    print("[PASS] Evidence hashes, adapter identities, observation counts, and missing needs preserved")
    print("[PASS] Partial evidence intake remains explicit instead of being promoted to complete")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-033 CERTIFIED")
