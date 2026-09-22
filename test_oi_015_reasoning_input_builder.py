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
    RoutedEvidenceOrchestrator,
)
from qseries_v2.observation_intelligence.oi_015_reasoning_input_builder import (
    OI_015_REVISION,
    OracleReasoningInputBuilder,
    verify_reasoning_input_builder,
)

NOW = datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc)


def acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="coinbase.public.spot",
                source_kind="market_data",
                provider="Coinbase",
                adapter_id="adapter.coinbase.spot.v1",
            ),
            external_observation_id="BTC-USD-OI015",
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


def orchestration():
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

    resolver = ObservationRequirementResolver(
        (profile,)
    )

    registry = default_source_registry()

    router = ObservationSourceRoutingRegistry(
        registry,
        default_observation_route_rules(),
    )

    acquisition_engine = RoutedObservationAcquisitionEngine(
        adapter_registry=registry,
        routing_registry=router,
        bindings=(
            AdapterAcquisitionBinding(
                adapter_id="adapter.coinbase.spot.v1",
                acquire_callable=acquire,
            ),
            AdapterAcquisitionBinding(
                adapter_id="adapter.kalshi.v1",
                acquire_callable=lambda request: (),
            ),
        ),
    )

    return RoutedEvidenceOrchestrator(
        requirement_resolver=resolver,
        acquisition_engine=acquisition_engine,
    ).orchestrate(
        profile_id="profile.asset_state",
        query_id="query.asset.reasoning",
        evaluated_at=NOW,
    )


class TestOI015(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_input_builder()
        )

    def test_build(self):
        value = OracleReasoningInputBuilder().build(
            orchestration(),
            built_at=NOW,
        )

        self.assertEqual(
            len(value.evidence_items),
            1,
        )

        self.assertTrue(
            value.complete_required_evidence
        )

        self.assertEqual(
            value.missing_evidence_count,
            0,
        )

    def test_non_predictive(self):
        value = OracleReasoningInputBuilder().build(
            orchestration(),
            built_at=NOW,
        )

        self.assertFalse(
            value.predictive
        )

        self.assertTrue(
            value.read_only
        )

    def test_lineage(self):
        value = OracleReasoningInputBuilder().build(
            orchestration(),
            built_at=NOW,
        )

        item = value.evidence_items[0]

        self.assertEqual(
            item.adapter_id,
            "adapter.coinbase.spot.v1",
        )

        self.assertEqual(
            item.freshness_status,
            "fresh",
        )

    def test_deterministic(self):
        builder = OracleReasoningInputBuilder()

        a = builder.build(
            orchestration(),
            built_at=NOW,
        )

        b = builder.build(
            orchestration(),
            built_at=NOW,
        )

        self.assertEqual(
            a.input_hash,
            b.input_hash,
        )

    def test_side_effects(self):
        builder = OracleReasoningInputBuilder()

        self.assertTrue(
            builder.read_only
        )

        self.assertFalse(
            builder.network_allowed
        )

        self.assertFalse(
            builder.persistence_allowed
        )

        self.assertFalse(
            builder.publication_allowed
        )

        self.assertFalse(
            builder.execution_allowed
        )

        self.assertFalse(
            builder.qseries_execution_allowed
        )

        self.assertFalse(
            builder.prediction_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-015 CERTIFICATION TEST")
    print(" ORACLE REASONING INPUT BUILDER — CORRECTION V2")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI015
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-015")
    print(f"[PASS] Revision: {OI_015_REVISION}")
    print("[PASS] Routed evidence converts to deterministic Oracle reasoning input")
    print("[PASS] Source lineage, freshness, facts, and missing-evidence state preserved")
    print("[PASS] Reasoning input remains evidence-only and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-015 CERTIFIED")
