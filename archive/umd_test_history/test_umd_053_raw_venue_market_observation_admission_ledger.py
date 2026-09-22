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
    build_umd_053_certification_manifest,
    certify_raw_venue_market_observation_admission_ledger,
    certify_umd_053_foundation,
)

FIXED = datetime(
    2026,
    8,
    7,
    2,
    35,
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
    source_id: str = "SOURCE-A",
    venue_market_id: str = "MARKET-A",
):
    observation_hash = digest(
        f"umd-053:{suffix}:observation"
    )
    request_hash = digest(
        f"umd-053:{suffix}:request"
    )
    request_decision_hash = digest(
        f"umd-053:{suffix}:request-decision"
    )
    source_contract_hash = digest(
        f"umd-053:{suffix}:source-contract"
    )
    source_registry_hash = digest(
        f"umd-053:{suffix}:source-registry"
    )
    raw_payload_hash = digest(
        f"umd-053:{suffix}:raw-payload"
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
            f"fixture://umd-053/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedRawVenueMarketObservationAdmissionDecision(
        observation_id=f"observation-{suffix}",
        observation_hash=observation_hash,
        request_id=f"request-{suffix}",
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
            f"fixture://umd-053/entry/{number}",
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


def ledger(entries):
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-053",
        revision=UMD_053_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            ()
            if not entries
            else (entries[-1].entry_hash,)
        ),
        source_refs=(
            "fixture://umd-053/ledger",
        ),
        created_at=FIXED,
    )
    return ReadOnlyRawVenueMarketObservationAdmissionLedger(
        entries=tuple(entries),
        ledger_lineage=lineage,
    )


class TestUMD053(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_053_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-053")

    def test_ledger_certifies(self) -> None:
        first = entry(
            1,
            decision("a", True, "SOURCE-A", "MARKET-A"),
            None,
        )
        second = entry(
            2,
            decision("b", False, "SOURCE-B", "MARKET-B"),
            first.entry_hash,
        )
        item = ledger((first, second))
        result = (
            certify_raw_venue_market_observation_admission_ledger(
                item
            )
        )
        self.assertTrue(result["certified"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["rejected_count"], 1)
        self.assertEqual(result["source_count"], 2)
        self.assertEqual(result["venue_market_count"], 2)

    def test_deterministic(self) -> None:
        value = decision("a")
        first = entry(1, value, None)
        second = entry(1, value, None)
        self.assertEqual(first.entry_id, second.entry_id)
        self.assertEqual(first.entry_hash, second.entry_hash)

    def test_sequence_gap_rejected(self) -> None:
        first = entry(1, decision("a"), None)
        second = entry(
            3,
            decision("b"),
            first.entry_hash,
        )
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_hash_chain_rejected(self) -> None:
        first = entry(1, decision("a"), None)
        second = entry(
            2,
            decision("b"),
            digest("wrong"),
        )
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_duplicate_observation_rejected(self) -> None:
        value = decision("a")
        first = entry(1, value, None)
        second = entry(
            2,
            value,
            first.entry_hash,
        )
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_lookup_indexes(self) -> None:
        first = entry(
            1,
            decision(
                "a",
                True,
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
                "SOURCE-A",
                "MARKET-A",
            ),
            first.entry_hash,
        )
        item = ledger((first, second))

        self.assertIs(item.get(first.entry_id), first)
        self.assertIs(
            item.get_by_observation_id(
                first.decision.observation_id
            ),
            first,
        )
        self.assertIs(
            item.get_by_observation_hash(
                first.decision.observation_hash
            ),
            first,
        )
        self.assertIs(
            item.get_by_decision_id(
                first.decision.decision_id
            ),
            first,
        )
        self.assertEqual(
            item.list_by_source_id("SOURCE-A"),
            (first, second),
        )
        self.assertEqual(
            item.list_by_venue_market_id("MARKET-A"),
            (first, second),
        )
        self.assertIs(item.latest_admitted(), first)

    def test_lineage_requires_latest_hash(self) -> None:
        first = entry(1, decision("a"), None)
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-053",
            revision=UMD_053_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-053/bad-ledger",
            ),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            ReadOnlyRawVenueMarketObservationAdmissionLedger(
                entries=(first,),
                ledger_lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        first = entry(1, decision("a"), None)
        item = ledger((first,))
        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            first.sequence_number = 2
        with self.assertRaises(TypeError):
            first.metadata["read_only"] = False
        with self.assertRaises(TypeError):
            item._by_observation_id["changed"] = first

    def test_side_effects(self) -> None:
        manifest = build_umd_053_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-053 CERTIFICATION TEST")
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION LEDGER"
    )
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD053
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_053_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-052 consumed read-only")
    print("[PASS] Exact UMD-052 observation-admission decision consumed")
    print("[PASS] Append-only sequence and previous-entry hash chain certified")
    print("[PASS] Duplicate observation and decision replay rejected")
    print("[PASS] Immutable observation, source, and venue-market indexes certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-053 CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION LEDGER CERTIFIED")
