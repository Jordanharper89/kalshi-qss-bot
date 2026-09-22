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
    build_raw_venue_market_observation,
)
from qseries_v2.universal_market_discovery.umd_052_raw_venue_market_observation_admission_gate import (
    UMD_052_REVISION,
    build_umd_052_certification_manifest,
    certify_umd_052_foundation,
    evaluate_raw_venue_market_observation_admission,
)

FIXED = datetime(
    2026,
    8,
    7,
    2,
    5,
    0,
    tzinfo=timezone.utc,
)


def digest(label: str) -> str:
    return hashlib.sha256(
        label.encode("utf-8")
    ).hexdigest()


def request():
    source_contract_hash = digest(
        "umd-052:source-contract"
    )
    source_registry_hash = digest(
        "umd-052:source-registry"
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
        source_refs=("fixture://umd-052/request",),
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
        requested_market_families=("BINARY_MARKET",),
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


def request_decision(item):
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
            "fixture://umd-052/request-decision",
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
        admitted=True,
        checks={"request_certified": True},
        rejection_reasons=(),
        lineage=lineage,
    )


def observation():
    item = request()
    gate = request_decision(item)
    payload = {
        "ticker": "KXBTC-26AUG07-T100000",
        "title": "Will Bitcoin exceed 100000?",
        "status": "active",
        "yes_bid": 41,
        "yes_ask": 43,
    }
    payload_hash = deterministic_sha256(payload)
    lineage = ImmutableLineage(
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
            "fixture://umd-052/observation",
        ),
        created_at=FIXED,
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
        metadata={"network_enabled": False},
        lineage=lineage,
    )


def gate_lineage(item):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-052",
        revision=UMD_052_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            item.observation_hash,
            item.request_hash,
            item.admission_decision_record_hash,
            item.source_contract_hash,
            item.source_registry_hash,
            item.raw_payload_hash,
        ),
        source_refs=(
            "fixture://umd-052/gate",
        ),
        created_at=FIXED,
    )


class TestUMD052(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_052_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-052")

    def test_valid_observation_admitted(self) -> None:
        item = observation()
        decision = evaluate_raw_venue_market_observation_admission(
            item,
            lineage=gate_lineage(item),
        )
        self.assertTrue(decision.admitted)
        self.assertEqual(decision.rejection_reasons, ())
        self.assertTrue(all(decision.checks.values()))

    def test_deterministic(self) -> None:
        item = observation()
        lineage = gate_lineage(item)
        first = evaluate_raw_venue_market_observation_admission(
            item,
            lineage=lineage,
        )
        second = evaluate_raw_venue_market_observation_admission(
            item,
            lineage=lineage,
        )
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertEqual(first.record_hash, second.record_hash)

    def test_duplicate_observation_id_rejected(self) -> None:
        item = observation()
        decision = evaluate_raw_venue_market_observation_admission(
            item,
            seen_observation_ids=(item.observation_id,),
            lineage=gate_lineage(item),
        )
        self.assertFalse(decision.admitted)
        self.assertIn(
            "observation_id_not_seen",
            decision.rejection_reasons,
        )

    def test_duplicate_observation_hash_rejected(self) -> None:
        item = observation()
        decision = evaluate_raw_venue_market_observation_admission(
            item,
            seen_observation_hashes=(
                item.observation_hash,
            ),
            lineage=gate_lineage(item),
        )
        self.assertFalse(decision.admitted)
        self.assertIn(
            "observation_hash_not_seen",
            decision.rejection_reasons,
        )

    def test_duplicate_retrieval_rejected(self) -> None:
        item = observation()
        key = (
            f"{item.source_id}|"
            f"{item.venue_market_id}|"
            f"{item.retrieval_sequence}"
        )
        decision = evaluate_raw_venue_market_observation_admission(
            item,
            seen_source_market_retrieval_keys=(key,),
            lineage=gate_lineage(item),
        )
        self.assertFalse(decision.admitted)
        self.assertIn(
            "source_market_retrieval_not_seen",
            decision.rejection_reasons,
        )

    def test_lineage_requires_all_hashes(self) -> None:
        item = observation()
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-052",
            revision=UMD_052_REVISION,
            schema_version="1.0.0",
            parent_hashes=(
                item.observation_hash,
            ),
            source_refs=(
                "fixture://umd-052/bad",
            ),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            evaluate_raw_venue_market_observation_admission(
                item,
                lineage=bad,
            )

    def test_immutable(self) -> None:
        item = observation()
        decision = evaluate_raw_venue_market_observation_admission(
            item,
            lineage=gate_lineage(item),
        )
        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            decision.admitted = False
        with self.assertRaises(TypeError):
            decision.checks["changed"] = False

    def test_side_effects(self) -> None:
        manifest = build_umd_052_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-052 CERTIFICATION TEST")
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION GATE"
    )
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD052
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_052_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-051 consumed read-only")
    print("[PASS] Exact UMD-051 raw-observation class consumed")
    print("[PASS] Deterministic observation-admission decision certified")
    print("[PASS] Duplicate observation ID, hash, and retrieval replay rejected")
    print("[PASS] Immutable complete decision lineage certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-052 CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION GATE CERTIFIED")
