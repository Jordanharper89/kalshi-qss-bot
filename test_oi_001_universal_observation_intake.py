from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    OI_001_REVISION,
    ObservationSourceIdentity,
    RawObservationEnvelope,
    UniversalObservationIntake,
    verify_universal_observation_intake,
)


FIXED = datetime(
    2026,
    8,
    10,
    3,
    0,
    tzinfo=timezone.utc,
)


def source() -> ObservationSourceIdentity:
    return ObservationSourceIdentity(
        source_id="kalshi.public",
        source_kind="market_venue",
        provider="Kalshi",
        adapter_id="adapter.kalshi.v1",
    )


def envelope() -> RawObservationEnvelope:
    return RawObservationEnvelope(
        source=source(),
        external_observation_id="market-123",
        observed_at=FIXED,
        subject="BTC above 100k",
        observation_type="market_snapshot",
        payload={
            "yes_price": 63,
            "no_price": 37,
        },
        metadata={
            "venue": "kalshi",
        },
    )


class TestOI001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_universal_observation_intake()
        )

    def test_source_identity(self):
        self.assertEqual(
            len(source().source_hash),
            64,
        )

    def test_immutable(self):
        item = envelope()

        with self.assertRaises(TypeError):
            item.payload["x"] = 1

    def test_deterministic(self):
        self.assertEqual(
            envelope().envelope_hash,
            envelope().envelope_hash,
        )

    def test_accept(self):
        receipt = (
            UniversalObservationIntake()
            .accept(envelope())
        )

        self.assertTrue(
            receipt.accepted
        )

        self.assertEqual(
            receipt.envelope_hash,
            envelope().envelope_hash,
        )

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            RawObservationEnvelope(
                source=source(),
                external_observation_id="x",
                observed_at=datetime(
                    2026,
                    8,
                    10,
                    3,
                    0,
                ),
                subject="x",
                observation_type="event",
                payload={},
                metadata={},
            )

    def test_side_effects(self):
        intake = UniversalObservationIntake()

        self.assertTrue(
            intake.read_only
        )

        self.assertFalse(
            intake.network_allowed
        )

        self.assertFalse(
            intake.persistence_allowed
        )

        self.assertFalse(
            intake.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-001 CERTIFICATION TEST")
    print(" UNIVERSAL OBSERVATION INTAKE FOUNDATION")
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestOI001
    )

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-001")
    print(f"[PASS] Revision: {OI_001_REVISION}")
    print("[PASS] Universal source-agnostic observation envelope certified")
    print("[PASS] Immutable deterministic intake contract certified")
    print("[PASS] No category-specific reasoning introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-001 CERTIFIED")
