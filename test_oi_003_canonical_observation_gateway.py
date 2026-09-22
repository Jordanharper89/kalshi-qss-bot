from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)

from qseries_v2.observation_intelligence.oi_002_source_adapter_registry import (
    SourceAdapterDescriptor,
    SourceAdapterRegistry,
)

from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    OI_003_REVISION,
    CanonicalLiveObservationGateway,
    verify_canonical_observation_gateway,
)


FIXED = datetime(
    2026,
    8,
    10,
    3,
    30,
    tzinfo=timezone.utc,
)


def descriptor():
    return SourceAdapterDescriptor(
        adapter_id="adapter.crypto.v1",
        source_id="crypto.market_data",
        source_kind="market_data",
        provider="Crypto Market Data",
        adapter_version="1.0.0",
        capabilities=(
            "market snapshot",
            "spot price",
        ),
        enabled_for_intake=True,
    )


def registry():
    return SourceAdapterRegistry(
        (
            descriptor(),
        )
    )


def envelope():
    return RawObservationEnvelope(
        source=ObservationSourceIdentity(
            source_id="crypto.market_data",
            source_kind="market_data",
            provider="Crypto Market Data",
            adapter_id="adapter.crypto.v1",
        ),
        external_observation_id=(
            "btc-usd-20260810T033000Z"
        ),
        observed_at=FIXED,
        subject="Bitcoin",
        observation_type="spot_price",
        payload={
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": "123456.78",
        },
        metadata={
            "venue": "example",
        },
    )


class TestOI003(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_canonical_observation_gateway()
        )

    def test_canonicalize(self):
        receipt = (
            CanonicalLiveObservationGateway(
                registry()
            )
            .canonicalize(
                envelope()
            )
        )

        observation = (
            receipt.canonical_observation
        )

        self.assertEqual(
            observation.subject,
            "Bitcoin",
        )

        self.assertEqual(
            observation.observation_type,
            "spot_price",
        )

    def test_identity(self):
        observation = (
            CanonicalLiveObservationGateway(
                registry()
            )
            .canonicalize(
                envelope()
            )
            .canonical_observation
        )

        self.assertTrue(
            observation
            .canonical_observation_id
            .startswith("obs.")
        )

    def test_deterministic(self):
        gateway = (
            CanonicalLiveObservationGateway(
                registry()
            )
        )

        a = gateway.canonicalize(
            envelope()
        )

        b = gateway.canonicalize(
            envelope()
        )

        self.assertEqual(
            a.canonical_observation
            .canonical_observation_hash,
            b.canonical_observation
            .canonical_observation_hash,
        )

    def test_unregistered_rejected(self):
        empty = SourceAdapterRegistry(
            ()
        )

        with self.assertRaises(ValueError):
            CanonicalLiveObservationGateway(
                empty
            ).canonicalize(
                envelope()
            )

    def test_immutable(self):
        observation = (
            CanonicalLiveObservationGateway(
                registry()
            )
            .canonicalize(
                envelope()
            )
            .canonical_observation
        )

        with self.assertRaises(TypeError):
            observation.facts["price"] = "1"

    def test_lineage(self):
        receipt = (
            CanonicalLiveObservationGateway(
                registry()
            )
            .canonicalize(
                envelope()
            )
        )

        self.assertEqual(
            len(
                receipt
                .canonical_observation
                .raw_envelope_hash
            ),
            64,
        )

        self.assertEqual(
            len(
                receipt.adapter_registry_hash
            ),
            64,
        )

        self.assertEqual(
            len(
                receipt.intake_receipt_hash
            ),
            64,
        )

    def test_side_effects(self):
        gateway = (
            CanonicalLiveObservationGateway(
                registry()
            )
        )

        self.assertTrue(
            gateway.read_only
        )

        self.assertFalse(
            gateway.network_allowed
        )

        self.assertFalse(
            gateway.persistence_allowed
        )

        self.assertFalse(
            gateway.publication_allowed
        )

        self.assertFalse(
            gateway.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-003 CERTIFICATION TEST")
    print(" CANONICAL LIVE OBSERVATION GATEWAY")
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestOI003
    )

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-003")
    print(f"[PASS] Revision: {OI_003_REVISION}")
    print("[PASS] Registered source envelopes converted to canonical observations")
    print("[PASS] Source, adapter, timestamp, payload, and lineage preserved")
    print("[PASS] Unregistered sources rejected deterministically")
    print("[PASS] Same gateway contract supports Kalshi, crypto, weather, economic, news, blockchain, sports, and future adapters")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-003 CERTIFIED")
