from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
)
from qseries_v2.observation_intelligence.oi_029_observation_acquisition_plan import (
    ObservationAcquisitionPlan,
    ObservationAcquisitionPlanItem,
)
from qseries_v2.observation_intelligence.oi_030_oracle_observation_request_package import (
    OI_030_REVISION,
    OracleObservationRequestPackageBuilder,
    verify_oracle_observation_request_package,
)

NOW = datetime(
    2026,
    8,
    10,
    19,
    0,
    tzinfo=timezone.utc,
)


def query():
    return OracleExplanationQueryEngine(
        default_explanation_profile_map()
    ).resolve(
        query_id="query.astros",
        text="Explain why the Astros strikeout edge moved",
        subject_hint="Astros strikeouts",
        domain="sports",
    )


def plan():
    return ObservationAcquisitionPlan(
        plan_id="plan.astros",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        items=(
            ObservationAcquisitionPlanItem(
                ordinal=1,
                need_id="profile.market_explanation.need.1",
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
                need_id="profile.market_explanation.need.2",
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


class TestOI030(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_observation_request_package()
        )

    def test_build(self):
        package = (
            OracleObservationRequestPackageBuilder()
            .build(
                request_id="request.astros",
                query=query(),
                acquisition_plan=plan(),
                assembled_at=NOW,
            )
        )

        self.assertEqual(
            package.requested_adapter_ids,
            ("adapter.kalshi.v1",),
        )

        self.assertEqual(
            package.missing_need_ids,
            ("profile.market_explanation.need.2",),
        )

        self.assertFalse(
            package.complete_adapter_coverage
        )

    def test_query_preserved(self):
        package = (
            OracleObservationRequestPackageBuilder()
            .build(
                request_id="request.astros",
                query=query(),
                acquisition_plan=plan(),
                assembled_at=NOW,
            )
        )

        self.assertEqual(
            package.query_kind,
            "explanation",
        )

        self.assertEqual(
            package.subject_hint,
            "Astros strikeouts",
        )

    def test_deterministic(self):
        builder = OracleObservationRequestPackageBuilder()

        a = builder.build(
            request_id="request.astros",
            query=query(),
            acquisition_plan=plan(),
            assembled_at=NOW,
        )

        b = builder.build(
            request_id="request.astros",
            query=query(),
            acquisition_plan=plan(),
            assembled_at=NOW,
        )

        self.assertEqual(
            a.package_hash,
            b.package_hash,
        )

    def test_side_effects(self):
        builder = OracleObservationRequestPackageBuilder()

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
    print(" OI-030 CERTIFICATION TEST")
    print(" ORACLE OBSERVATION REQUEST PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI030
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-030")
    print(f"[PASS] Revision: {OI_030_REVISION}")
    print("[PASS] Explanation query and acquisition plan packaged into deterministic Oracle observation request")
    print("[PASS] Requested adapters and missing observation capabilities remain explicit")
    print("[PASS] Request package is terminal-safe, read-only, and non-mutating")
    print("[PASS] Prediction, probability, scoring, publication, and execution disabled")
    print("[DONE] OI-030 CERTIFIED")
