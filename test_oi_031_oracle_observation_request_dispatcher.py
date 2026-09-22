from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
)
from qseries_v2.observation_intelligence.oi_012_routed_observation_acquisition import (
    AdapterAcquisitionBinding,
    RoutedObservationAcquisitionEngine,
)
from qseries_v2.observation_intelligence.oi_029_observation_acquisition_plan import (
    ObservationAcquisitionPlan,
    ObservationAcquisitionPlanItem,
)
from qseries_v2.observation_intelligence.oi_030_oracle_observation_request_package import (
    OracleObservationRequestPackage,
)
from qseries_v2.observation_intelligence.oi_031_oracle_observation_request_dispatcher import (
    OI_031_REVISION,
    OracleObservationRequestDispatcher,
    verify_oracle_observation_request_dispatcher,
)

NOW = datetime(2026, 8, 10, 20, 0, tzinfo=timezone.utc)


def kalshi_acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="kalshi.public",
                source_kind="market_venue",
                provider="Kalshi",
                adapter_id="adapter.kalshi.v1",
            ),
            external_observation_id="KX-ASTROS-OI031",
            observed_at=NOW,
            subject="Astros strikeouts",
            observation_type="market_snapshot",
            payload={
                "ticker": "KXASTROS",
                "yes_bid": 54,
                "yes_ask": 56,
            },
            metadata={
                "venue": "kalshi",
                "market_ticker": "KXASTROS",
            },
        ),
    )


def engine():
    registry = default_source_registry()

    return RoutedObservationAcquisitionEngine(
        adapter_registry=registry,
        routing_registry=ObservationSourceRoutingRegistry(
            registry,
            default_observation_route_rules(),
        ),
        bindings=(
            AdapterAcquisitionBinding(
                adapter_id="adapter.coinbase.spot.v1",
                acquire_callable=lambda request: (),
            ),
            AdapterAcquisitionBinding(
                adapter_id="adapter.kalshi.v1",
                acquire_callable=kalshi_acquire,
            ),
        ),
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


def request_package():
    return OracleObservationRequestPackage(
        request_id="request.astros",
        query_id="query.astros",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        profile_id="profile.market_explanation",
        acquisition_plan_hash="c" * 64,
        requested_adapter_ids=("adapter.kalshi.v1",),
        missing_need_ids=("profile.market_explanation.need.2",),
        complete_adapter_coverage=False,
        assembled_at=NOW,
        package_hash="d" * 64,
        read_only=True,
        predictive=False,
        terminal_mutation_allowed=False,
    )


class TestOI031(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_observation_request_dispatcher()
        )

    def test_dispatch(self):
        result = OracleObservationRequestDispatcher(
            engine()
        ).dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        self.assertEqual(result.covered_need_count, 1)
        self.assertEqual(result.missing_need_count, 1)
        self.assertEqual(result.acquired_observation_count, 1)

    def test_missing_need_not_invoked(self):
        result = OracleObservationRequestDispatcher(
            engine()
        ).dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        self.assertFalse(result.items[1].covered)
        self.assertIsNone(result.items[1].acquisition_hash)

    def test_adapter_identity_preserved(self):
        result = OracleObservationRequestDispatcher(
            engine()
        ).dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        self.assertEqual(
            result.items[0].adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_deterministic(self):
        dispatcher = OracleObservationRequestDispatcher(
            engine()
        )

        a = dispatcher.dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        b = dispatcher.dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        self.assertEqual(a.dispatch_hash, b.dispatch_hash)

    def test_side_effects(self):
        dispatcher = OracleObservationRequestDispatcher(
            engine()
        )

        self.assertTrue(dispatcher.read_only)
        self.assertFalse(dispatcher.persistence_allowed)
        self.assertFalse(dispatcher.publication_allowed)
        self.assertFalse(dispatcher.execution_allowed)
        self.assertFalse(dispatcher.qseries_execution_allowed)
        self.assertFalse(dispatcher.prediction_allowed)
        self.assertFalse(dispatcher.edge_score_allowed)
        self.assertFalse(dispatcher.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-031 CERTIFICATION TEST")
    print(" ORACLE OBSERVATION REQUEST DISPATCHER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI031
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-031")
    print(f"[PASS] Revision: {OI_031_REVISION}")
    print("[PASS] Certified observation request plans dispatch only through approved routed acquisition")
    print("[PASS] Missing capabilities are not invoked and remain explicit")
    print("[PASS] Adapter identity, evidence hash, and observation counts preserved")
    print("[PASS] Persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-031 CERTIFIED")
