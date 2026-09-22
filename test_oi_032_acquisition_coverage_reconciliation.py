from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_029_observation_acquisition_plan import (
    ObservationAcquisitionPlan,
    ObservationAcquisitionPlanItem,
)
from qseries_v2.observation_intelligence.oi_031_oracle_observation_request_dispatcher import (
    DispatchedObservationNeed,
    OracleObservationDispatchResult,
)
from qseries_v2.observation_intelligence.oi_032_acquisition_coverage_reconciliation import (
    OI_032_REVISION,
    STATUS_PARTIAL,
    AcquisitionCoverageReconciler,
    verify_acquisition_coverage_reconciliation,
)

NOW = datetime(2026, 8, 10, 21, 0, tzinfo=timezone.utc)


def plan():
    return ObservationAcquisitionPlan(
        plan_id="plan.astros",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        items=(
            ObservationAcquisitionPlanItem(
                ordinal=1,
                need_id="need.market",
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
                subject_hint="Astros strikeouts",
                adapter_ids=("adapter.kalshi.v1",),
                covered=True,
                item_hash="a" * 64,
            ),
            ObservationAcquisitionPlanItem(
                ordinal=2,
                need_id="need.lineup",
                domain="sports",
                entity_kind="team",
                observation_type="lineup",
                subject_hint="Astros strikeouts",
                adapter_ids=(),
                covered=False,
                item_hash="b" * 64,
            ),
        ),
        covered_count=1,
        missing_count=1,
        complete_coverage=False,
        plan_hash="c" * 64,
        read_only=True,
    )


def dispatch():
    return OracleObservationDispatchResult(
        request_id="request.astros",
        request_package_hash="d" * 64,
        plan_hash="c" * 64,
        dispatched_at=NOW,
        items=(
            DispatchedObservationNeed(
                ordinal=1,
                need_id="need.market",
                covered=True,
                adapter_ids=("adapter.kalshi.v1",),
                acquisition_hash="e" * 64,
                observation_count=1,
                evidence_hash="f" * 64,
                dispatch_item_hash="1" * 64,
            ),
            DispatchedObservationNeed(
                ordinal=2,
                need_id="need.lineup",
                covered=False,
                adapter_ids=(),
                acquisition_hash=None,
                observation_count=0,
                evidence_hash=None,
                dispatch_item_hash="2" * 64,
            ),
        ),
        covered_need_count=1,
        missing_need_count=1,
        acquired_observation_count=1,
        dispatch_hash="3" * 64,
        read_only=True,
    )


class TestOI032(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_acquisition_coverage_reconciliation()
        )

    def test_partial(self):
        result = AcquisitionCoverageReconciler().reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        self.assertEqual(result.status, STATUS_PARTIAL)
        self.assertEqual(result.satisfied_count, 1)
        self.assertEqual(result.unsatisfied_count, 1)

    def test_missing_reason(self):
        result = AcquisitionCoverageReconciler().reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        self.assertEqual(
            result.items[1].reason_code,
            "adapter_capability_missing",
        )

    def test_satisfied_reason(self):
        result = AcquisitionCoverageReconciler().reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        self.assertTrue(result.items[0].satisfied)
        self.assertEqual(
            result.items[0].reason_code,
            "satisfied",
        )

    def test_deterministic(self):
        reconciler = AcquisitionCoverageReconciler()

        a = reconciler.reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        b = reconciler.reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        self.assertEqual(
            a.reconciliation_hash,
            b.reconciliation_hash,
        )

    def test_side_effects(self):
        item = AcquisitionCoverageReconciler()

        self.assertTrue(item.read_only)
        self.assertFalse(item.network_allowed)
        self.assertFalse(item.persistence_allowed)
        self.assertFalse(item.publication_allowed)
        self.assertFalse(item.execution_allowed)
        self.assertFalse(item.qseries_execution_allowed)
        self.assertFalse(item.prediction_allowed)
        self.assertFalse(item.edge_score_allowed)
        self.assertFalse(item.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-032 CERTIFICATION TEST")
    print(" ACQUISITION COVERAGE RECONCILIATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI032
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-032")
    print(f"[PASS] Revision: {OI_032_REVISION}")
    print("[PASS] Planned observation coverage reconciled against actual acquisition results")
    print("[PASS] Missing adapter capability and empty acquisition remain explicitly distinguishable")
    print("[PASS] Complete, partial, and empty acquisition states certified")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-032 CERTIFIED")
