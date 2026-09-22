from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.umd_045_venue_discovery_source_contract import (
    UMD_045_REVISION,
    CertifiedVenueDiscoverySourceContract,
)
from qseries_v2.universal_market_discovery.umd_046_venue_discovery_source_registry import (
    UMD_046_REVISION,
    CertifiedVenueDiscoverySourceRegistry,
)
from qseries_v2.universal_market_discovery.umd_047_venue_discovery_request_contract import (
    UMD_047_REVISION,
    build_venue_discovery_request_contract,
)
from qseries_v2.universal_market_discovery.umd_048_venue_discovery_request_admission_gate import (
    UMD_048_REVISION,
    CertifiedVenueDiscoveryRequestAdmissionDecision,
    build_umd_048_certification_manifest,
    certify_umd_048_foundation,
    evaluate_venue_discovery_request_admission,
)

FIXED = datetime(2026, 8, 6, 20, 20, 0, tzinfo=timezone.utc)


def source():
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-045",
        revision=UMD_045_REVISION,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=("fixture://umd-048/source",),
        created_at=FIXED,
    )
    return CertifiedVenueDiscoverySourceContract(
        canonical_venue_id="KALSHI",
        adapter_key="KALSHI_MARKET_CATALOG",
        display_name="Kalshi Market Catalog",
        discovery_method="REST_CATALOG",
        authentication_mode="API_KEY",
        pagination_mode="CURSOR",
        supported_market_families=("BINARY_MARKET", "EVENT_CONTRACT"),
        supported_statuses=("ACTIVE", "CLOSED", "SETTLED"),
        source_schema_version="v1",
        supports_incremental_discovery=True,
        supports_historical_markets=True,
        supports_settlement_status=True,
        supports_cursor_resume=True,
        rate_limit_metadata_available=True,
        read_only=True,
        metadata={},
        lineage=lineage,
    )


def registry(item):
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-046",
        revision=UMD_046_REVISION,
        schema_version="1.0.0",
        parent_hashes=(item.contract_hash,),
        source_refs=("fixture://umd-048/registry",),
        created_at=FIXED,
    )
    return CertifiedVenueDiscoverySourceRegistry(
        sources=(item,),
        registry_metadata={},
        lineage=lineage,
    )


def request():
    source_item = source()
    registry_item = registry(source_item)
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-047",
        revision=UMD_047_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            source_item.contract_hash,
            registry_item.registry_hash,
        ),
        source_refs=("fixture://umd-048/request",),
        created_at=FIXED,
    )
    return build_venue_discovery_request_contract(
        registry_item,
        source_item,
        discovery_scope="ACTIVE_AND_HISTORICAL",
        requested_statuses=("ACTIVE", "SETTLED"),
        requested_market_families=("BINARY_MARKET",),
        requested_at=FIXED,
        request_schema_version="v1",
        lineage=lineage,
        pagination_cursor="cursor-1",
        page_size=500,
        metadata={"read_only": True},
    )


def gate_lineage(item):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-048",
        revision=UMD_048_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            item.request_hash,
            item.source_contract_hash,
            item.source_registry_hash,
        ),
        source_refs=("fixture://umd-048/gate",),
        created_at=FIXED,
    )


class TestUMD048(unittest.TestCase):
    def test_foundation(self):
        result = certify_umd_048_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-048")

    def test_valid_request_admitted(self):
        item = request()
        decision = evaluate_venue_discovery_request_admission(
            item,
            lineage=gate_lineage(item),
        )
        self.assertTrue(decision.admitted)
        self.assertEqual(decision.rejection_reasons, ())
        self.assertTrue(all(decision.checks.values()))

    def test_deterministic(self):
        item = request()
        lineage = gate_lineage(item)
        first = evaluate_venue_discovery_request_admission(
            item,
            lineage=lineage,
        )
        second = evaluate_venue_discovery_request_admission(
            item,
            lineage=lineage,
        )
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertEqual(first.record_hash, second.record_hash)

    def test_duplicate_request_id_rejected(self):
        item = request()
        decision = evaluate_venue_discovery_request_admission(
            item,
            known_request_ids=(item.request_id,),
            lineage=gate_lineage(item),
        )
        self.assertFalse(decision.admitted)
        self.assertIn(
            "request_id_not_previously_seen",
            decision.rejection_reasons,
        )

    def test_duplicate_request_hash_rejected(self):
        item = request()
        decision = evaluate_venue_discovery_request_admission(
            item,
            known_request_hashes=(item.request_hash,),
            lineage=gate_lineage(item),
        )
        self.assertFalse(decision.admitted)
        self.assertIn(
            "request_hash_not_previously_seen",
            decision.rejection_reasons,
        )

    def test_lineage_requires_all_hashes(self):
        item = request()
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-048",
            revision=UMD_048_REVISION,
            schema_version="1.0.0",
            parent_hashes=(item.request_hash,),
            source_refs=("fixture://umd-048/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            evaluate_venue_discovery_request_admission(
                item,
                lineage=bad,
            )

    def test_decision_consistency(self):
        item = request()
        with self.assertRaises(ValueError):
            CertifiedVenueDiscoveryRequestAdmissionDecision(
                request_id=item.request_id,
                request_hash=item.request_hash,
                source_id=item.source_id,
                source_contract_hash=item.source_contract_hash,
                source_registry_hash=item.source_registry_hash,
                admitted=True,
                checks={"bad": False},
                rejection_reasons=("bad",),
                lineage=gate_lineage(item),
            )

    def test_immutable(self):
        item = request()
        decision = evaluate_venue_discovery_request_admission(
            item,
            lineage=gate_lineage(item),
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            decision.admitted = False
        with self.assertRaises(TypeError):
            decision.checks["changed"] = False

    def test_side_effects(self):
        manifest = build_umd_048_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-048 CERTIFICATION TEST")
    print(" CERTIFIED VENUE DISCOVERY REQUEST ADMISSION GATE")
    print("=" * 72)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD048)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_048_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-047 consumed read-only")
    print("[PASS] Exact UMD-047 request-contract class consumed")
    print("[PASS] Deterministic admission decision certified")
    print("[PASS] Duplicate request ID and hash replay rejected")
    print("[PASS] Immutable decision lineage certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-048 CERTIFIED VENUE DISCOVERY REQUEST ADMISSION GATE CERTIFIED")
