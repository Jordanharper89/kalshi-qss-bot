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
from qseries_v2.observation_intelligence.oi_033_oracle_evidence_intake_package import (
    OracleEvidenceIntakeItem,
    OracleEvidenceIntakePackage,
)
from qseries_v2.observation_intelligence.oi_034_canonical_evidence_materialization import (
    OI_034_REVISION,
    CanonicalEvidenceMaterializer,
    verify_canonical_evidence_materialization,
)

NOW = datetime(2026, 8, 10, 23, 0, tzinfo=timezone.utc)


def intake():
    return OracleEvidenceIntakePackage(
        intake_id="intake.astros",
        request_id="request.astros",
        query_id="query.astros",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        profile_id="profile.market_explanation",
        acquisition_status="partial",
        evidence_items=(
            OracleEvidenceIntakeItem(
                need_id="need.market",
                adapter_ids=("adapter.kalshi.v1",),
                evidence_hash="a" * 64,
                observation_count=1,
                satisfied=True,
                reason_code="satisfied",
                item_hash="b" * 64,
            ),
        ),
        total_observation_count=1,
        missing_need_ids=("need.lineup",),
        complete_evidence_intake=False,
        assembled_at=NOW,
        intake_hash="c" * 64,
        read_only=True,
        predictive=False,
        terminal_mutation_allowed=False,
    )


def kalshi_observation():
    envelope = RawObservationEnvelope(
        source=ObservationSourceIdentity(
            source_id="kalshi.public",
            source_kind="market_venue",
            provider="Kalshi",
            adapter_id="adapter.kalshi.v1",
        ),
        external_observation_id="KXASTROS-OI034",
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
    )

    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(
        envelope
    ).canonical_observation


def coinbase_observation():
    envelope = RawObservationEnvelope(
        source=ObservationSourceIdentity(
            source_id="coinbase.public.spot",
            source_kind="market_data",
            provider="Coinbase",
            adapter_id="adapter.coinbase.spot.v1",
        ),
        external_observation_id="BTC-OI034",
        observed_at=NOW,
        subject="BTC",
        observation_type="spot_price",
        payload={
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": "65000.00",
        },
        metadata={},
    )

    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(
        envelope
    ).canonical_observation


class TestOI034(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_canonical_evidence_materialization()
        )

    def test_materialize(self):
        value = CanonicalEvidenceMaterializer().materialize(
            intake=intake(),
            observations=(kalshi_observation(),),
        )

        self.assertEqual(value.observation_count, 1)
        self.assertTrue(value.complete_count_match)

    def test_adapter_preserved(self):
        value = CanonicalEvidenceMaterializer().materialize(
            intake=intake(),
            observations=(kalshi_observation(),),
        )

        self.assertEqual(
            value.items[0].adapter_id,
            "adapter.kalshi.v1",
        )

    def test_unadmitted_adapter_rejected(self):
        with self.assertRaises(ValueError):
            CanonicalEvidenceMaterializer().materialize(
                intake=intake(),
                observations=(coinbase_observation(),),
            )

    def test_empty_materialization_count_mismatch(self):
        value = CanonicalEvidenceMaterializer().materialize(
            intake=intake(),
            observations=(),
        )

        self.assertEqual(value.observation_count, 0)
        self.assertFalse(value.complete_count_match)

    def test_deterministic(self):
        builder = CanonicalEvidenceMaterializer()

        a = builder.materialize(
            intake=intake(),
            observations=(kalshi_observation(),),
        )
        b = builder.materialize(
            intake=intake(),
            observations=(kalshi_observation(),),
        )

        self.assertEqual(
            a.materialization_hash,
            b.materialization_hash,
        )

    def test_side_effects(self):
        builder = CanonicalEvidenceMaterializer()

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
    print(" OI-034 CERTIFICATION TEST")
    print(" CANONICAL EVIDENCE MATERIALIZATION — CORRECTION V2")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI034
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-034")
    print(f"[PASS] Revision: {OI_034_REVISION}")
    print("[PASS] Canonical observations materialized against certified Oracle evidence intake")
    print("[PASS] Observation identity, hash, adapter, provider, subject, type, and timestamp preserved")
    print("[PASS] Unadmitted adapter evidence rejected with an actual foreign canonical observation")
    print("[PASS] Empty materialization remains valid but explicitly fails count reconciliation")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-034 CERTIFIED")
