from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_gate import (
    UMD_032_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
    build_umd_032_certification_manifest,
    certify_umd_032_foundation,
    verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate,
)

FIXED = datetime(
    2026,
    8,
    6,
    10,
    30,
    tzinfo=timezone.utc,
)
READ_MODEL_HASH = "a" * 64
REGISTRY_HASH = "b" * 64
LEDGER_HASH = "c" * 64


def lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-032",
        revision=UMD_032_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            READ_MODEL_HASH,
            REGISTRY_HASH,
            LEDGER_HASH,
        ),
        source_refs=(
            "fixture://umd-032/decision",
        ),
        created_at=FIXED,
    )


class TestUMD032(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_032_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate()
        )

    def test_decision_identity_deterministic(self) -> None:
        checks = {
            "read_model_hash_deterministic": True,
            "session_registry_hash_matches": True,
        }

        first = CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
            read_model_hash=READ_MODEL_HASH,
            session_registry_hash=REGISTRY_HASH,
            admission_ledger_hash=LEDGER_HASH,
            admitted=True,
            checks=checks,
            rejection_reasons=(),
            lineage=lineage(),
        )

        second = CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
            read_model_hash=READ_MODEL_HASH,
            session_registry_hash=REGISTRY_HASH,
            admission_ledger_hash=LEDGER_HASH,
            admitted=True,
            checks=dict(
                reversed(tuple(checks.items()))
            ),
            rejection_reasons=(),
            lineage=lineage(),
        )

        self.assertEqual(
            first.decision_id,
            second.decision_id,
        )
        self.assertEqual(
            first.record_hash,
            second.record_hash,
        )

    def test_rejected_decision_requires_matching_reasons(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
                read_model_hash=READ_MODEL_HASH,
                session_registry_hash=REGISTRY_HASH,
                admission_ledger_hash=LEDGER_HASH,
                admitted=False,
                checks={
                    "read_model_hash_deterministic": False
                },
                rejection_reasons=(
                    "wrong_reason",
                ),
                lineage=lineage(),
            )

    def test_admitted_decision_rejects_failures(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
                read_model_hash=READ_MODEL_HASH,
                session_registry_hash=REGISTRY_HASH,
                admission_ledger_hash=LEDGER_HASH,
                admitted=True,
                checks={
                    "read_model_hash_deterministic": False
                },
                rejection_reasons=(),
                lineage=lineage(),
            )

    def test_lineage_requires_all_parent_hashes(
        self,
    ) -> None:
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-032",
            revision=UMD_032_REVISION,
            schema_version="1.0.0",
            parent_hashes=(READ_MODEL_HASH,),
            source_refs=(
                "fixture://umd-032/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
                read_model_hash=READ_MODEL_HASH,
                session_registry_hash=REGISTRY_HASH,
                admission_ledger_hash=LEDGER_HASH,
                admitted=True,
                checks={
                    "read_model_hash_deterministic": True
                },
                rejection_reasons=(),
                lineage=bad_lineage,
            )

    def test_decision_is_immutable(self) -> None:
        item = CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
            read_model_hash=READ_MODEL_HASH,
            session_registry_hash=REGISTRY_HASH,
            admission_ledger_hash=LEDGER_HASH,
            admitted=True,
            checks={
                "read_model_hash_deterministic": True
            },
            rejection_reasons=(),
            lineage=lineage(),
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.admitted = False

        with self.assertRaises(TypeError):
            item.checks[
                "read_model_hash_deterministic"
            ] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_032_certification_manifest()

        self.assertEqual(
            manifest.gate_mode,
            "read_only_read_model_validation",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-032 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL ADMISSION GATE"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD032
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_032_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-031 "
        "consumed read-only"
    )
    print(
        "[PASS] Read-model admission decision IDs deterministic"
    )
    print(
        "[PASS] Read-model hash validation certified"
    )
    print(
        "[PASS] Session registry hash binding certified"
    )
    print(
        "[PASS] Admission ledger hash binding certified"
    )
    print(
        "[PASS] Session and execution membership counts certified"
    )
    print(
        "[PASS] Latest-session consistency certified"
    )
    print(
        "[PASS] Immutable read-model admission decisions certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-032 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION READ MODEL ADMISSION GATE CERTIFIED"
    )
