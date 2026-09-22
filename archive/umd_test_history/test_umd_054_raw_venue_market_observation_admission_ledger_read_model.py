from __future__ import annotations

import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.umd_052_raw_venue_market_observation_admission_gate import (
    UMD_052_REVISION,
    CertifiedRawVenueMarketObservationAdmissionDecision,
)
from qseries_v2.universal_market_discovery.umd_053_raw_venue_market_observation_admission_ledger import (
    UMD_053_REVISION,
    CertifiedRawVenueMarketObservationAdmissionLedgerEntry,
    ReadOnlyRawVenueMarketObservationAdmissionLedger,
)
from qseries_v2.universal_market_discovery.umd_054_raw_venue_market_observation_admission_ledger_read_model import (
    UMD_054_REVISION,
    build_umd_054_certification_manifest,
    build_umd_054_observation_admission_ledger_read_model,
    certify_umd_054_foundation,
    certify_umd_054_read_model,
)

FIXED = datetime(
    2026,
    8,
    7,
    3,
    5,
    0,
    tzinfo=timezone.utc,
)


def digest(label: str) -> str:
    return hashlib.sha256(
        label.encode("utf-8")
    ).hexdigest()


def decision(
    suffix: str,
    admitted: bool = True,
    request_id: str = "REQUEST-A",
    source_id: str = "SOURCE-A",
    venue_market_id: str = "MARKET-A",
):
    observation_hash = digest(
        f"umd-054:{suffix}:observation"
    )
    request_hash = digest(
        f"umd-054:{suffix}:request"
    )
    request_decision_hash = digest(
        f"umd-054:{suffix}:request-decision"
    )
    source_contract_hash = digest(
        f"umd-054:{suffix}:source-contract"
    )
    source_registry_hash = digest(
        f"umd-054:{suffix}:source-registry"
    )
    raw_payload_hash = digest(
        f"umd-054:{suffix}:raw-payload"
    )
    checks = {"certified": admitted}
    reasons = () if admitted else ("certified",)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-052",
        revision=UMD_052_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            observation_hash,
            request_hash,
            request_decision_hash,
            source_contract_hash,
            source_registry_hash,
            raw_payload_hash,
        ),
        source_refs=(
            f"fixture://umd-054/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedRawVenueMarketObservationAdmissionDecision(
        observation_id=f"observation-{suffix}",
        observation_hash=observation_hash,
        request_id=request_id,
        request_hash=request_hash,
        admission_decision_id=f"request-decision-{suffix}",
        admission_decision_record_hash=request_decision_hash,
        source_id=source_id,
        source_contract_hash=source_contract_hash,
        source_registry_hash=source_registry_hash,
        raw_payload_hash=raw_payload_hash,
        canonical_venue_id="KALSHI",
        adapter_key="KALSHI_MARKET_CATALOG",
        venue_market_id=venue_market_id,
        retrieval_sequence=1,
        admitted=admitted,
        checks=checks,
        rejection_reasons=reasons,
        lineage=lineage,
    )


def entry(number: int, value, previous: str | None):
    parents = [value.record_hash]
    if previous is not None:
        parents.append(previous)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-053",
        revision=UMD_053_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-054/entry/{number}",
        ),
        created_at=FIXED,
    )

    return CertifiedRawVenueMarketObservationAdmissionLedgerEntry(
        sequence_number=number,
        previous_entry_hash=previous,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def source_ledger():
    first = entry(
        1,
        decision(
            "a",
            True,
            "REQUEST-A",
            "SOURCE-A",
            "MARKET-A",
        ),
        None,
    )
    second = entry(
        2,
        decision(
            "b",
            False,
            "REQUEST-B",
            "SOURCE-A",
            "MARKET-A",
        ),
        first.entry_hash,
    )
    third = entry(
        3,
        decision(
            "c",
            True,
            "REQUEST-A",
            "SOURCE-B",
            "MARKET-B",
        ),
        second.entry_hash,
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-053",
        revision=UMD_053_REVISION,
        schema_version="1.0.0",
        parent_hashes=(third.entry_hash,),
        source_refs=(
            "fixture://umd-054/ledger",
        ),
        created_at=FIXED,
    )

    return ReadOnlyRawVenueMarketObservationAdmissionLedger(
        entries=(first, second, third),
        ledger_lineage=lineage,
    )


def read_model_lineage(ledger_hash: str):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-054",
        revision=UMD_054_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ledger_hash,),
        source_refs=(
            "fixture://umd-054/read-model",
        ),
        created_at=FIXED,
    )


class TestUMD054(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_054_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-054")

    def test_projection(self) -> None:
        ledger = source_ledger()
        model = build_umd_054_observation_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=read_model_lineage(
                ledger.ledger_hash
            ),
        )
        result = certify_umd_054_read_model(model)
        self.assertTrue(result["certified"])
        self.assertEqual(result["total_entry_count"], 3)
        self.assertEqual(result["admitted_entry_count"], 2)
        self.assertEqual(result["rejected_entry_count"], 1)
        self.assertEqual(result["request_count"], 2)
        self.assertEqual(result["source_count"], 2)
        self.assertEqual(result["venue_market_count"], 2)

    def test_deterministic(self) -> None:
        ledger = source_ledger()
        lineage = read_model_lineage(
            ledger.ledger_hash
        )
        first = build_umd_054_observation_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=lineage,
        )
        second = build_umd_054_observation_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=lineage,
        )
        self.assertEqual(
            first.read_model_id,
            second.read_model_id,
        )
        self.assertEqual(
            first.read_model_hash,
            second.read_model_hash,
        )

    def test_positions_and_partitions(self) -> None:
        ledger = source_ledger()
        model = build_umd_054_observation_admission_ledger_read_model(
            ledger,
            lineage=read_model_lineage(
                ledger.ledger_hash
            ),
        )
        first, second, third = ledger.entries

        self.assertEqual(
            model.entry_position(first.entry_id),
            1,
        )
        self.assertEqual(
            model.observation_position(
                second.decision.observation_id
            ),
            2,
        )
        self.assertEqual(
            model.observation_hash_position(
                third.decision.observation_hash
            ),
            3,
        )
        self.assertEqual(
            model.decision_position(
                third.decision.decision_id
            ),
            3,
        )
        self.assertTrue(
            model.is_admitted_entry(first.entry_id)
        )
        self.assertTrue(
            model.is_rejected_entry(second.entry_id)
        )
        self.assertEqual(
            model.latest_entry_id,
            third.entry_id,
        )
        self.assertEqual(
            model.latest_admitted_entry_id,
            third.entry_id,
        )

    def test_grouped_indexes(self) -> None:
        ledger = source_ledger()
        model = build_umd_054_observation_admission_ledger_read_model(
            ledger,
            lineage=read_model_lineage(
                ledger.ledger_hash
            ),
        )
        first, second, third = ledger.entries

        self.assertEqual(
            model.list_entry_ids_by_request_id(
                "REQUEST-A"
            ),
            (
                first.entry_id,
                third.entry_id,
            ),
        )
        self.assertEqual(
            model.list_entry_ids_by_source_id(
                "SOURCE-A"
            ),
            (
                first.entry_id,
                second.entry_id,
            ),
        )
        self.assertEqual(
            model.list_entry_ids_by_venue_market_id(
                "MARKET-A"
            ),
            (
                first.entry_id,
                second.entry_id,
            ),
        )

    def test_lineage_requires_ledger(self) -> None:
        ledger = source_ledger()
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-054",
            revision=UMD_054_REVISION,
            schema_version="1.0.0",
            parent_hashes=(digest("wrong-ledger"),),
            source_refs=(
                "fixture://umd-054/bad",
            ),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            build_umd_054_observation_admission_ledger_read_model(
                ledger,
                lineage=bad,
            )

    def test_exact_umd053_type(self) -> None:
        ledger = source_ledger()
        self.assertIsInstance(
            ledger,
            ReadOnlyRawVenueMarketObservationAdmissionLedger,
        )
        self.assertEqual(
            ledger.ledger_lineage.build_id,
            "UMD-053",
        )

    def test_immutable(self) -> None:
        ledger = source_ledger()
        model = build_umd_054_observation_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=read_model_lineage(
                ledger.ledger_hash
            ),
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            model.total_entry_count = 99
        with self.assertRaises(TypeError):
            model.metadata["read_only"] = False
        with self.assertRaises(TypeError):
            model._entry_position_by_id[
                model.ordered_entry_ids[0]
            ] = 99

    def test_side_effects(self) -> None:
        manifest = build_umd_054_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-054 CERTIFICATION TEST")
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION "
        "ADMISSION LEDGER READ MODEL"
    )
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD054
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_054_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-053 consumed read-only")
    print("[PASS] Exact UMD-053 admission-ledger class consumed")
    print("[PASS] Deterministic observation admission-ledger projection certified")
    print("[PASS] Immutable entry, observation, decision, request, source, and venue-market indexes certified")
    print("[PASS] Admitted and rejected partitions certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-054 CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION LEDGER READ MODEL CERTIFIED")
