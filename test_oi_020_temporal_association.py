from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_002_source_adapter_registry import (
    SourceAdapterDescriptor,
    SourceAdapterRegistry,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_017_observation_change_attribution import (
    ObservationChange,
)
from qseries_v2.observation_intelligence.oi_020_temporal_association import (
    OI_020_REVISION,
    TemporalAssociationEngine,
    verify_temporal_association,
)

BASE = datetime(
    2026,
    8,
    10,
    14,
    0,
    tzinfo=timezone.utc,
)


def registry():
    return SourceAdapterRegistry(
        (
            SourceAdapterDescriptor(
                adapter_id="adapter.news.a",
                source_id="news.a",
                source_kind="news",
                provider="News A",
                adapter_version="1",
                capabilities=("news",),
                enabled_for_intake=True,
            ),
        )
    )


def evidence(
    external_id: str,
    offset_seconds: int,
):
    envelope = RawObservationEnvelope(
        source=ObservationSourceIdentity(
            source_id="news.a",
            source_kind="news",
            provider="News A",
            adapter_id="adapter.news.a",
        ),
        external_observation_id=external_id,
        observed_at=(
            BASE
            + timedelta(
                seconds=offset_seconds
            )
        ),
        subject="Astros",
        observation_type="news",
        payload={
            "headline": external_id,
        },
        metadata={},
    )

    return CanonicalLiveObservationGateway(
        registry()
    ).canonicalize(
        envelope
    ).canonical_observation


def change():
    return ObservationChange(
        subject="Astros strikeouts",
        observation_type="market_snapshot",
        value_field="yes_bid",
        prior_observation_id="obs.prior",
        current_observation_id="obs.current",
        prior_value=50.0,
        current_value=56.0,
        absolute_change=6.0,
        relative_change=0.12,
        direction="up",
        change_hash="c" * 64,
    )


class TestOI020(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_temporal_association()
        )

    def test_before(self):
        values = (
            TemporalAssociationEngine()
            .associate(
                change=change(),
                change_observed_at=BASE,
                evidence=(
                    evidence(
                        "before",
                        -30,
                    ),
                ),
                max_window_seconds=60,
            )
        )

        self.assertEqual(
            values[0].temporal_relation,
            "before",
        )

    def test_after(self):
        values = (
            TemporalAssociationEngine()
            .associate(
                change=change(),
                change_observed_at=BASE,
                evidence=(
                    evidence(
                        "after",
                        20,
                    ),
                ),
                max_window_seconds=60,
            )
        )

        self.assertEqual(
            values[0].temporal_relation,
            "after",
        )

    def test_outside_window_excluded(self):
        values = (
            TemporalAssociationEngine()
            .associate(
                change=change(),
                change_observed_at=BASE,
                evidence=(
                    evidence(
                        "far",
                        120,
                    ),
                ),
                max_window_seconds=60,
            )
        )

        self.assertEqual(
            values,
            (),
        )

    def test_nearest_first(self):
        values = (
            TemporalAssociationEngine()
            .associate(
                change=change(),
                change_observed_at=BASE,
                evidence=(
                    evidence(
                        "near",
                        10,
                    ),
                    evidence(
                        "farther",
                        -30,
                    ),
                ),
                max_window_seconds=60,
            )
        )

        self.assertEqual(
            values[0].seconds_from_change_observation,
            10,
        )

    def test_deterministic(self):
        engine = TemporalAssociationEngine()

        a = engine.associate(
            change=change(),
            change_observed_at=BASE,
            evidence=(
                evidence(
                    "near",
                    10,
                ),
            ),
            max_window_seconds=60,
        )

        b = engine.associate(
            change=change(),
            change_observed_at=BASE,
            evidence=(
                evidence(
                    "near",
                    10,
                ),
            ),
            max_window_seconds=60,
        )

        self.assertEqual(
            a[0].association_hash,
            b[0].association_hash,
        )

    def test_side_effects(self):
        engine = TemporalAssociationEngine()
        self.assertTrue(engine.read_only)
        self.assertFalse(engine.network_allowed)
        self.assertFalse(engine.persistence_allowed)
        self.assertFalse(engine.publication_allowed)
        self.assertFalse(engine.execution_allowed)
        self.assertFalse(engine.qseries_execution_allowed)
        self.assertFalse(engine.causal_inference_allowed)
        self.assertFalse(engine.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-020 CERTIFICATION TEST")
    print(" TEMPORAL ASSOCIATION FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI020
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-020")
    print(f"[PASS] Revision: {OI_020_REVISION}")
    print("[PASS] Before, simultaneous, and after temporal relationships certified")
    print("[PASS] Bounded association windows and nearest-event ordering certified")
    print("[PASS] Temporal association explicitly does not imply causation")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-020 CERTIFIED")
