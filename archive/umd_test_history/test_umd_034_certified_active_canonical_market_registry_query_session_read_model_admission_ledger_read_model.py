from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_gate import (
    UMD_032_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger import (
    UMD_033_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model import (
    UMD_034_REVISION,
    build_active_market_query_session_read_model_admission_ledger_read_model,
    build_umd_034_certification_manifest,
    certify_active_market_query_session_read_model_admission_ledger_read_model,
    certify_umd_034_foundation,
)

FIXED = datetime(
    2026,
    8,
    6,
    5,
    38,
    0,
    tzinfo=timezone.utc,
)


def decision(
    suffix: str,
    admitted: bool = True,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionDecision:
    read_model_hash = (suffix.lower() * 64)[:64]
    session_registry_hash = (
        chr(ord(suffix.lower()) + 1) * 64
    )[:64]
    admission_ledger_hash = (
        chr(ord(suffix.lower()) + 2) * 64
    )[:64]

    checks = {
        "read_model_hash_deterministic": admitted,
    }
    rejection_reasons = (
        ()
        if admitted
        else ("read_model_hash_deterministic",)
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-032",
        revision=UMD_032_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            read_model_hash,
            session_registry_hash,
            admission_ledger_hash,
        ),
        source_refs=(
            f"fixture://umd-034/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
        read_model_hash=read_model_hash,
        session_registry_hash=session_registry_hash,
        admission_ledger_hash=admission_ledger_hash,
        admitted=admitted,
        checks=checks,
        rejection_reasons=rejection_reasons,
        lineage=lineage,
    )


def ledger_entry(
    sequence_number: int,
    value: CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
    previous_entry_hash: str | None,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry:
    parents = [value.record_hash]
    if previous_entry_hash is not None:
        parents.append(previous_entry_hash)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-033",
        revision=UMD_033_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-034/entry/{sequence_number}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry(
        sequence_number=sequence_number,
        previous_entry_hash=previous_entry_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={"fixture": True},
        lineage=lineage,
    )


def source_ledger() -> ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger:
    first = ledger_entry(
        1,
        decision("a", admitted=True),
        None,
    )
    second = ledger_entry(
        2,
        decision("d", admitted=False),
        first.entry_hash,
    )
    third = ledger_entry(
        3,
        decision("c", admitted=True),
        second.entry_hash,
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-033",
        revision=UMD_033_REVISION,
        schema_version="1.0.0",
        parent_hashes=(third.entry_hash,),
        source_refs=("fixture://umd-034/ledger",),
        created_at=FIXED,
    )

    return ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger(
        entries=(first, second, third),
        ledger_lineage=lineage,
    )


def read_model_lineage(
    ledger_hash: str,
) -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-034",
        revision=UMD_034_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ledger_hash,),
        source_refs=("fixture://umd-034/read-model",),
        created_at=FIXED,
    )


class TestUMD034(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        result = certify_umd_034_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-034")

    def test_projection_certifies(self) -> None:
        ledger = source_ledger()
        model = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                metadata={"read_only": True},
                lineage=read_model_lineage(
                    ledger.ledger_hash
                ),
            )
        )

        result = (
            certify_active_market_query_session_read_model_admission_ledger_read_model(
                model
            )
        )

        self.assertTrue(result["certified"])
        self.assertEqual(result["total_entry_count"], 3)
        self.assertEqual(result["admitted_entry_count"], 2)
        self.assertEqual(result["rejected_entry_count"], 1)

    def test_projection_is_deterministic(self) -> None:
        ledger = source_ledger()
        lineage = read_model_lineage(
            ledger.ledger_hash
        )

        first = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                metadata={"read_only": True},
                lineage=lineage,
            )
        )
        second = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                metadata={"read_only": True},
                lineage=lineage,
            )
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
        model = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                lineage=read_model_lineage(
                    ledger.ledger_hash
                ),
            )
        )

        first = ledger.entries[0]
        second = ledger.entries[1]
        third = ledger.entries[2]

        self.assertEqual(
            model.entry_position(first.entry_id),
            1,
        )
        self.assertEqual(
            model.read_model_position(
                second.decision.read_model_hash
            ),
            2,
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

    def test_lineage_requires_ledger_hash(self) -> None:
        ledger = source_ledger()
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-034",
            revision=UMD_034_REVISION,
            schema_version="1.0.0",
            parent_hashes=("f" * 64,),
            source_refs=("fixture://umd-034/bad",),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        ledger = source_ledger()
        model = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                metadata={"read_only": True},
                lineage=read_model_lineage(
                    ledger.ledger_hash
                ),
            )
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

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_034_certification_manifest()

        self.assertEqual(
            manifest.read_model_mode,
            "deterministic_read_only_projection",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-034 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION "
        "READ MODEL ADMISSION LEDGER READ MODEL"
    )
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD034
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_034_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-033 "
        "consumed read-only"
    )
    print(
        "[PASS] UMD-033 admission ledger projected deterministically"
    )
    print(
        "[PASS] Ordered ledger-entry identity preserved"
    )
    print(
        "[PASS] Read-model and decision indexes certified"
    )
    print(
        "[PASS] Admitted/rejected partition certified"
    )
    print(
        "[PASS] Latest entry and latest admitted entry certified"
    )
    print(
        "[PASS] Immutable lineage bound to source ledger hash"
    )
    print(
        "[PASS] Replay equality verified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-034 CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL ADMISSION LEDGER READ MODEL CERTIFIED"
    )
