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
from qseries_v2.observation_intelligence.oi_013_observation_requirement_resolution import (
    ObservationRequirement,
    ObservationRequirementResolver,
    build_requirement_profile,
)
from qseries_v2.observation_intelligence.oi_014_routed_evidence_orchestrator import (
    OI_014_REVISION,
    RoutedEvidenceOrchestrator,
    verify_routed_evidence_orchestrator,
)

NOW = datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc)


def coinbase_acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="coinbase.public.spot",
                source_kind="market_data",
                provider="Coinbase",
                adapter_id="adapter.coinbase.spot.v1",
            ),
            external_observation_id="BTC-USD-OI014",
            observed_at=NOW,
            subject="BTC",
            observation_type="spot_price",
            payload={
                "product_id": "BTC-USD",
                "symbol": "BTC",
                "quote_currency": "USD",
                "price": "100.0",
            },
            metadata={"venue": "coinbase"},
        ),
    )


def requirement_resolver():
    profile = build_requirement_profile(
        "profile.asset_state",
        (
            ObservationRequirement(
                requirement_id="requirement.spot",
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
                required=True,
                reason="current asset state",
            ),
        ),
    )

    return ObservationRequirementResolver(
        (profile,)
    )


def acquisition_engine():
    registry = default_source_registry()
    router = ObservationSourceRoutingRegistry(
        registry,
        default_observation_route_rules(),
    )

    return RoutedObservationAcquisitionEngine(
        adapter_registry=registry,
        routing_registry=router,
        bindings=(
            AdapterAcquisitionBinding(
                adapter_id="adapter.coinbase.spot.v1",
                acquire_callable=coinbase_acquire,
            ),
            AdapterAcquisitionBinding(
                adapter_id="adapter.kalshi.v1",
                acquire_callable=lambda request: (),
            ),
        ),
    )


class TestOI014(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_routed_evidence_orchestrator()
        )

    def test_orchestration(self):
        value = RoutedEvidenceOrchestrator(
            requirement_resolver=requirement_resolver(),
            acquisition_engine=acquisition_engine(),
        ).orchestrate(
            profile_id="profile.asset_state",
            query_id="query.asset",
            evaluated_at=NOW,
        )

        self.assertEqual(value.required_count, 1)
        self.assertEqual(value.satisfied_count, 1)
        self.assertEqual(value.missing_count, 0)

    def test_health(self):
        value = RoutedEvidenceOrchestrator(
            requirement_resolver=requirement_resolver(),
            acquisition_engine=acquisition_engine(),
        ).orchestrate(
            profile_id="profile.asset_state",
            query_id="query.asset",
            evaluated_at=NOW,
        )

        self.assertEqual(
            value.results[0].health[0].freshness_status,
            "fresh",
        )

    def test_deterministic(self):
        orchestrator = RoutedEvidenceOrchestrator(
            requirement_resolver=requirement_resolver(),
            acquisition_engine=acquisition_engine(),
        )

        a = orchestrator.orchestrate(
            profile_id="profile.asset_state",
            query_id="query.asset",
            evaluated_at=NOW,
        )

        b = orchestrator.orchestrate(
            profile_id="profile.asset_state",
            query_id="query.asset",
            evaluated_at=NOW,
        )

        self.assertEqual(
            a.orchestration_hash,
            b.orchestration_hash,
        )

    def test_side_effects(self):
        value = RoutedEvidenceOrchestrator(
            requirement_resolver=requirement_resolver(),
            acquisition_engine=acquisition_engine(),
        )

        self.assertTrue(value.read_only)
        self.assertFalse(value.persistence_allowed)
        self.assertFalse(value.publication_allowed)
        self.assertFalse(value.execution_allowed)
        self.assertFalse(value.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-014 CERTIFICATION TEST")
    print(" ROUTED EVIDENCE ORCHESTRATOR")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI014
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-014")
    print(f"[PASS] Revision: {OI_014_REVISION}")
    print("[PASS] Requirement profiles drive routed acquisition")
    print("[PASS] Routed evidence receives freshness health")
    print("[PASS] Satisfied and missing required evidence counted deterministically")
    print("[PASS] No prediction or edge scoring introduced")
    print("[PASS] Persistence, publication, and execution disabled")
    print("[DONE] OI-014 CERTIFIED")
