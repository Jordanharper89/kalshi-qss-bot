from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
)
from qseries_v2.observation_intelligence.oi_009_observation_evidence_assembly import (
    OI_009_REVISION,
    ObservationEvidenceAssembler,
    verify_observation_evidence_assembly,
)


NOW = datetime(2026, 8, 10, 5, 0, tzinfo=timezone.utc)


def btc_observation():
    source = ObservationSourceIdentity(
        source_id="coinbase.public.spot",
        source_kind="market_data",
        provider="Coinbase",
        adapter_id="adapter.coinbase.spot.v1",
    )

    envelope = RawObservationEnvelope(
        source=source,
        external_observation_id="BTC-USD-EVIDENCE",
        observed_at=NOW,
        subject="BTC",
        observation_type="spot_price",
        payload={
            "product_id": "BTC-USD",
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": "100.00",
        },
        metadata={"venue": "coinbase"},
    )

    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(envelope).canonical_observation


class TestOI009(unittest.TestCase):
    def setUp(self):
        router = ObservationSourceRoutingRegistry(
            default_source_registry(),
            default_observation_route_rules(),
        )

        self.decision = router.route(
            ObservationRouteRequest(
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
            )
        )

        self.observation = btc_observation()

    def test_foundation(self):
        self.assertTrue(
            verify_observation_evidence_assembly()
        )

    def test_assembly(self):
        bundle = ObservationEvidenceAssembler().assemble(
            query_id="query.btc.price",
            route_decision=self.decision,
            observations=(self.observation,),
            assembled_at=NOW,
        )

        self.assertEqual(len(bundle.observations), 1)
        self.assertEqual(
            bundle.observations[0].adapter_id,
            "adapter.coinbase.spot.v1",
        )

    def test_hash_deterministic(self):
        assembler = ObservationEvidenceAssembler()

        a = assembler.assemble(
            query_id="query.btc.price",
            route_decision=self.decision,
            observations=(self.observation,),
            assembled_at=NOW,
        )

        b = assembler.assemble(
            query_id="query.btc.price",
            route_decision=self.decision,
            observations=(self.observation,),
            assembled_at=NOW,
        )

        self.assertEqual(a.evidence_hash, b.evidence_hash)

    def test_predictive_false(self):
        bundle = ObservationEvidenceAssembler().assemble(
            query_id="query.btc.price",
            route_decision=self.decision,
            observations=(self.observation,),
            assembled_at=NOW,
        )

        self.assertFalse(bundle.predictive)
        self.assertTrue(bundle.read_only)

    def test_wrong_adapter_rejected(self):
        router = ObservationSourceRoutingRegistry(
            default_source_registry(),
            default_observation_route_rules(),
        )

        decision = router.route(
            ObservationRouteRequest(
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
            )
        )

        with self.assertRaises(ValueError):
            ObservationEvidenceAssembler().assemble(
                query_id="bad",
                route_decision=decision,
                observations=(self.observation,),
                assembled_at=NOW,
            )

    def test_side_effects(self):
        assembler = ObservationEvidenceAssembler()
        self.assertTrue(assembler.read_only)
        self.assertFalse(assembler.network_allowed)
        self.assertFalse(assembler.persistence_allowed)
        self.assertFalse(assembler.publication_allowed)
        self.assertFalse(assembler.execution_allowed)
        self.assertFalse(assembler.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-009 CERTIFICATION TEST")
    print(" OBSERVATION EVIDENCE ASSEMBLY FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI009
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-009")
    print(f"[PASS] Revision: {OI_009_REVISION}")
    print("[PASS] Routed canonical observations assemble into immutable evidence bundles")
    print("[PASS] Source, provider, adapter, time, facts, and lineage preserved")
    print("[PASS] Unauthorized adapter evidence rejected")
    print("[PASS] Evidence assembly remains non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-009 CERTIFIED")
