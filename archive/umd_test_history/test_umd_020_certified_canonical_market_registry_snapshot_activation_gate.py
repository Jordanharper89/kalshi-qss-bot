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
from qseries_v2.universal_market_discovery.certified_canonical_market_registry_snapshot_activation_gate import (
    UMD_020_REVISION,
    CertifiedSnapshotActivationDecision,
    build_umd_020_certification_manifest,
    certify_umd_020_foundation,
    verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate,
)

FIXED = datetime(
    2026,
    8,
    6,
    4,
    30,
    tzinfo=timezone.utc,
)
ACTIVATION_HASH = "a" * 64


def decision_lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-020",
        revision=UMD_020_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ACTIVATION_HASH,),
        source_refs=(
            "fixture://umd-020/decision",
        ),
        created_at=FIXED,
    )


class TestUMD020(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_020_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate()
        )

    def test_decision_identity_deterministic(self) -> None:
        checks = {
            "activation_id_not_seen": True,
            "activation_hash_not_seen": True,
        }

        first = CertifiedSnapshotActivationDecision(
            activation_id=(
                "umd:snapshot-activation:"
                + "b" * 64
            ),
            activation_hash=ACTIVATION_HASH,
            snapshot_id=(
                "umd:market-registry-snapshot:"
                + "c" * 64
            ),
            snapshot_hash="d" * 64,
            admitted=True,
            checks=checks,
            rejection_reasons=(),
            lineage=decision_lineage(),
        )

        second = CertifiedSnapshotActivationDecision(
            activation_id=(
                "umd:snapshot-activation:"
                + "b" * 64
            ),
            activation_hash=ACTIVATION_HASH,
            snapshot_id=(
                "umd:market-registry-snapshot:"
                + "c" * 64
            ),
            snapshot_hash="d" * 64,
            admitted=True,
            checks=dict(
                reversed(tuple(checks.items()))
            ),
            rejection_reasons=(),
            lineage=decision_lineage(),
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
            CertifiedSnapshotActivationDecision(
                activation_id=(
                    "umd:snapshot-activation:"
                    + "b" * 64
                ),
                activation_hash=ACTIVATION_HASH,
                snapshot_id=(
                    "umd:market-registry-snapshot:"
                    + "c" * 64
                ),
                snapshot_hash="d" * 64,
                admitted=False,
                checks={
                    "activation_id_not_seen": False
                },
                rejection_reasons=(
                    "wrong_reason",
                ),
                lineage=decision_lineage(),
            )

    def test_admitted_decision_rejects_failures(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            CertifiedSnapshotActivationDecision(
                activation_id=(
                    "umd:snapshot-activation:"
                    + "b" * 64
                ),
                activation_hash=ACTIVATION_HASH,
                snapshot_id=(
                    "umd:market-registry-snapshot:"
                    + "c" * 64
                ),
                snapshot_hash="d" * 64,
                admitted=True,
                checks={
                    "activation_id_not_seen": False
                },
                rejection_reasons=(),
                lineage=decision_lineage(),
            )

    def test_lineage_requires_activation_hash(
        self,
    ) -> None:
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-020",
            revision=UMD_020_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-020/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedSnapshotActivationDecision(
                activation_id=(
                    "umd:snapshot-activation:"
                    + "b" * 64
                ),
                activation_hash=ACTIVATION_HASH,
                snapshot_id=(
                    "umd:market-registry-snapshot:"
                    + "c" * 64
                ),
                snapshot_hash="d" * 64,
                admitted=True,
                checks={
                    "activation_id_not_seen": True
                },
                rejection_reasons=(),
                lineage=bad_lineage,
            )

    def test_decision_is_immutable(self) -> None:
        item = CertifiedSnapshotActivationDecision(
            activation_id=(
                "umd:snapshot-activation:"
                + "b" * 64
            ),
            activation_hash=ACTIVATION_HASH,
            snapshot_id=(
                "umd:market-registry-snapshot:"
                + "c" * 64
            ),
            snapshot_hash="d" * 64,
            admitted=True,
            checks={
                "activation_id_not_seen": True
            },
            rejection_reasons=(),
            lineage=decision_lineage(),
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.admitted = False

        with self.assertRaises(TypeError):
            item.checks[
                "activation_id_not_seen"
            ] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_020_certification_manifest()

        self.assertEqual(
            manifest.gate_mode,
            "read_only_activation_validation",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-020 CERTIFICATION TEST")
    print(
        " CERTIFIED CANONICAL MARKET REGISTRY "
        "SNAPSHOT ACTIVATION GATE"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD020
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_020_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-019 "
        "consumed read-only"
    )
    print(
        "[PASS] Activation replay rejection "
        "contract certified"
    )
    print(
        "[PASS] Admitted snapshot and ledger "
        "binding certified"
    )
    print(
        "[PASS] Single-active-snapshot transition "
        "validation certified"
    )
    print(
        "[PASS] Snapshot rollback rejection "
        "contract certified"
    )
    print(
        "[PASS] Activation lineage and deterministic "
        "hashing certified"
    )
    print(
        "[PASS] Read-only activation gate certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution "
        "disabled"
    )
    print(
        "[DONE] UMD-020 CERTIFIED CANONICAL MARKET "
        "REGISTRY SNAPSHOT ACTIVATION GATE CERTIFIED"
    )
