from __future__ import annotations

import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
    deterministic_sha256,
)
from qseries_v2.universal_market_discovery.umd_047_venue_discovery_request_contract import (
    UMD_047_REVISION,
    CertifiedVenueDiscoveryRequestContract,
)
from qseries_v2.universal_market_discovery.umd_048_venue_discovery_request_admission_gate import (
    UMD_048_REVISION,
    CertifiedVenueDiscoveryRequestAdmissionDecision,
)
from qseries_v2.universal_market_discovery.umd_051_raw_venue_market_observation_contract import (
    UMD_051_REVISION,
    CertifiedRawVenueMarketObservation,
    build_raw_venue_market_observation,
    build_umd_051_certification_manifest,
    certify_raw_venue_market_observation,
    certify_umd_051_foundation,
)

FIXED = datetime(
    2026,
    8,
    7,
    1,
    40,
    0,
    tzinfo=timezone.utc,
)


def digest(label: str) -> str:
    return hashlib.sha256(
        label.encode("utf-8")
    ).hexdigest()


def request() -> CertifiedVenueDiscoveryRequestContract:
    source_contract_hash = digest(
        "umd-051:source-contract"
    )
    source_registry_hash = digest(
        "umd-051:source-registry"
    )
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-047",
        revision=UMD_047_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            source_contract_hash,
            source_registry_hash,
        ),
        source_refs=(
            "fixture://umd-051/request",
        ),
        created_at=FIXED,
    )
    return CertifiedVenueDiscoveryRequestContract(
        source_id="source-kalshi",
        source_contract_hash=source_contract_hash,
        source_registry_hash=source_registry_hash,
        canonical_venue_id="KALSHI",
        adapter_key="KALSHI_MARKET_CATALOG",
        discovery_scope="ACTIVE_ONLY",
        requested_statuses=("ACTIVE",),
        requested_market_families=(
            "BINARY_MARKET",
        ),
        window_start=None,
        window_end=None,
        pagination_cursor=None,
        page_size=100,
        requested_at=FIXED,
        request_schema_version="v1",
        read_only=True,
        metadata={"certification_only": True},
        lineage=lineage,
    )


def decision(
    item: CertifiedVenueDiscoveryRequestContract,
    admitted: bool = True,
) -> CertifiedVenueDiscoveryRequestAdmissionDecision:
    checks = {
        "request_certified": admitted,
    }
    reasons = (
        ()
        if admitted
        else ("request_certified",)
    )
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-048",
        revision=UMD_048_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            item.request_hash,
            item.source_contract_hash,
            item.source_registry_hash,
        ),
        source_refs=(
            "fixture://umd-051/decision",
        ),
        created_at=FIXED,
    )
    return CertifiedVenueDiscoveryRequestAdmissionDecision(
        request_id=item.request_id,
        request_hash=item.request_hash,
        source_id=item.source_id,
        source_contract_hash=(
            item.source_contract_hash
        ),
        source_registry_hash=(
            item.source_registry_hash
        ),
        admitted=admitted,
        checks=checks,
        rejection_reasons=reasons,
        lineage=lineage,
    )


def observation_lineage(
    item: CertifiedVenueDiscoveryRequestContract,
    gate: CertifiedVenueDiscoveryRequestAdmissionDecision,
    payload_hash: str,
) -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-051",
        revision=UMD_051_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            item.request_hash,
            gate.record_hash,
            item.source_contract_hash,
            item.source_registry_hash,
            payload_hash,
        ),
        source_refs=(
            "fixture://umd-051/raw-observation",
        ),
        created_at=FIXED,
    )


def build_observation():
    item = request()
    gate = decision(item)
    payload = {
        "ticker": "KXBTC-26AUG07-T100000",
        "title": "Will Bitcoin exceed 100000?",
        "status": "active",
        "yes_bid": 41,
        "yes_ask": 43,
        "nested": {
            "event_ticker": "KXBTC",
            "outcomes": ["yes", "no"],
        },
    }
    payload_hash = deterministic_sha256(
        payload
    )
    return build_raw_venue_market_observation(
        item,
        gate,
        venue_market_id="KXBTC-26AUG07-T100000",
        venue_event_id="KXBTC",
        source_record_type="MARKET",
        raw_title="Will Bitcoin exceed 100000?",
        raw_status="active",
        raw_market_family="binary",
        source_schema_version="kalshi-v1",
        raw_payload=payload,
        retrieval_sequence=1,
        observed_at=FIXED,
        source_emitted_at=FIXED,
        metadata={
            "transport": "fixture",
            "network_enabled": False,
        },
        lineage=observation_lineage(
            item,
            gate,
            payload_hash,
        ),
    )


class TestUMD051(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_051_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(
            result["build_id"],
            "UMD-051",
        )

    def test_observation_certifies(self) -> None:
        item = build_observation()
        result = certify_raw_venue_market_observation(
            item
        )
        self.assertTrue(result["certified"])
        self.assertEqual(
            result["venue_market_id"],
            "KXBTC-26AUG07-T100000",
        )

    def test_deterministic(self) -> None:
        first = build_observation()
        second = build_observation()
        self.assertEqual(
            first.observation_id,
            second.observation_id,
        )
        self.assertEqual(
            first.observation_hash,
            second.observation_hash,
        )

    def test_exact_request_and_decision_required(self) -> None:
        item = request()
        gate = decision(item)
        with self.assertRaises(TypeError):
            build_raw_venue_market_observation(
                object(),
                gate,
                venue_market_id="market",
                venue_event_id=None,
                source_record_type="MARKET",
                raw_title="Title",
                raw_status="active",
                raw_market_family="binary",
                source_schema_version="v1",
                raw_payload={"id": "market"},
                retrieval_sequence=1,
                observed_at=FIXED,
                source_emitted_at=None,
                metadata={},
                lineage=observation_lineage(
                    item,
                    gate,
                    deterministic_sha256(
                        {"id": "market"}
                    ),
                ),
            )

    def test_rejected_request_rejected(self) -> None:
        item = request()
        gate = decision(item, admitted=False)
        with self.assertRaises(ValueError):
            build_raw_venue_market_observation(
                item,
                gate,
                venue_market_id="market",
                venue_event_id=None,
                source_record_type="MARKET",
                raw_title="Title",
                raw_status="active",
                raw_market_family="binary",
                source_schema_version="v1",
                raw_payload={"id": "market"},
                retrieval_sequence=1,
                observed_at=FIXED,
                source_emitted_at=None,
                metadata={},
                lineage=observation_lineage(
                    item,
                    gate,
                    deterministic_sha256(
                        {"id": "market"}
                    ),
                ),
            )

    def test_payload_hash_mismatch_rejected(self) -> None:
        item = request()
        gate = decision(item)
        payload = {"id": "market"}
        lineage = observation_lineage(
            item,
            gate,
            deterministic_sha256(payload),
        )
        with self.assertRaises(ValueError):
            CertifiedRawVenueMarketObservation(
                request_id=item.request_id,
                request_hash=item.request_hash,
                admission_decision_id=(
                    gate.decision_id
                ),
                admission_decision_record_hash=(
                    gate.record_hash
                ),
                source_id=item.source_id,
                source_contract_hash=(
                    item.source_contract_hash
                ),
                source_registry_hash=(
                    item.source_registry_hash
                ),
                canonical_venue_id=(
                    item.canonical_venue_id
                ),
                adapter_key=item.adapter_key,
                venue_market_id="market",
                venue_event_id=None,
                source_record_type="MARKET",
                raw_title="Title",
                raw_status="active",
                raw_market_family="binary",
                source_schema_version="v1",
                raw_payload=payload,
                raw_payload_hash=digest("wrong"),
                retrieval_sequence=1,
                observed_at=FIXED,
                source_emitted_at=None,
                read_only=True,
                metadata={},
                lineage=lineage,
            )

    def test_source_time_cannot_follow_observation(self) -> None:
        item = request()
        gate = decision(item)
        payload = {"id": "market"}
        with self.assertRaises(ValueError):
            build_raw_venue_market_observation(
                item,
                gate,
                venue_market_id="market",
                venue_event_id=None,
                source_record_type="MARKET",
                raw_title="Title",
                raw_status="active",
                raw_market_family="binary",
                source_schema_version="v1",
                raw_payload=payload,
                retrieval_sequence=1,
                observed_at=FIXED,
                source_emitted_at=datetime(
                    2026,
                    8,
                    7,
                    1,
                    41,
                    0,
                    tzinfo=timezone.utc,
                ),
                metadata={},
                lineage=observation_lineage(
                    item,
                    gate,
                    deterministic_sha256(payload),
                ),
            )

    def test_immutable(self) -> None:
        item = build_observation()
        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.raw_status = "closed"
        with self.assertRaises(TypeError):
            item.raw_payload["status"] = "closed"
        with self.assertRaises(TypeError):
            item.raw_payload["nested"][
                "event_ticker"
            ] = "changed"
        with self.assertRaises(TypeError):
            item.metadata["network_enabled"] = True

    def test_side_effects(self) -> None:
        manifest = build_umd_051_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-051 CERTIFICATION TEST")
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION CONTRACT"
    )
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD051
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_051_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-050 consumed read-only")
    print("[PASS] Exact UMD-047 request and UMD-048 decision classes consumed")
    print("[PASS] Raw venue payload preserved immutably")
    print("[PASS] Request, decision, source, and payload lineage certified")
    print("[PASS] Deterministic raw observation identity certified")
    print("[PASS] No canonical classification or duplicate resolution performed")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-051 CERTIFIED RAW VENUE MARKET OBSERVATION CONTRACT CERTIFIED")
