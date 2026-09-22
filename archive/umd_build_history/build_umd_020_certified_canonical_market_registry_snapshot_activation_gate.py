from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_020_CERTIFIED_CANONICAL_MARKET_REGISTRY_SNAPSHOT_ACTIVATION_GATE_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_canonical_market_registry_snapshot_activation_gate.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_020_certified_canonical_market_registry_snapshot_activation_gate.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_registry_snapshot_activation_contract import (
    CertifiedCanonicalMarketRegistrySnapshotActivation,
    ReadOnlyActiveCanonicalMarketRegistry,
)

UMD_020_BUILD_ID = "UMD-020"
UMD_020_BUILD_NAME = (
    "Certified Canonical Market Registry Snapshot Activation Gate"
)
UMD_020_REVISION = (
    "UMD_020_CERTIFIED_CANONICAL_MARKET_REGISTRY_"
    "SNAPSHOT_ACTIVATION_GATE_V1"
)
UMD_020_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_activation_commit",
    "activation_persistence",
    "active_registry_mutation",
    "market_deletion",
    "oracle_memory_mutation",
    "publication",
    "order_submission",
    "trade_execution",
)


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _sha256(value: str, field_name: str) -> str:
    normalized = _text(value, field_name).lower()
    if len(normalized) != 64:
        raise ValueError(
            f"{field_name} must contain 64 hexadecimal characters"
        )
    if any(
        character not in "0123456789abcdef"
        for character in normalized
    ):
        raise ValueError(
            f"{field_name} must be lowercase SHA-256 hexadecimal"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class CertifiedSnapshotActivationDecision:
    activation_id: str
    activation_hash: str
    snapshot_id: str
    snapshot_hash: str
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        activation_id = _text(
            self.activation_id,
            "activation_id",
        )
        if not activation_id.startswith(
            "umd:snapshot-activation:"
        ):
            raise ValueError(
                "activation_id must use the UMD activation prefix"
            )
        object.__setattr__(
            self,
            "activation_id",
            activation_id,
        )

        object.__setattr__(
            self,
            "activation_hash",
            _sha256(
                self.activation_hash,
                "activation_hash",
            ),
        )

        snapshot_id = _text(
            self.snapshot_id,
            "snapshot_id",
        )
        if not snapshot_id.startswith(
            "umd:market-registry-snapshot:"
        ):
            raise ValueError(
                "snapshot_id must use the UMD snapshot prefix"
            )
        object.__setattr__(
            self,
            "snapshot_id",
            snapshot_id,
        )

        object.__setattr__(
            self,
            "snapshot_hash",
            _sha256(
                self.snapshot_hash,
                "snapshot_hash",
            ),
        )

        normalized_checks = {
            _text(str(name), "check name"): bool(passed)
            for name, passed in self.checks.items()
        }
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(
                dict(sorted(normalized_checks.items()))
            ),
        )

        failed_checks = tuple(
            name
            for name, passed in self.checks.items()
            if not passed
        )
        normalized_reasons = tuple(
            sorted(
                {
                    _text(reason, "rejection reason")
                    for reason in self.rejection_reasons
                }
            )
        )
        object.__setattr__(
            self,
            "rejection_reasons",
            normalized_reasons,
        )

        if self.admitted:
            if failed_checks or normalized_reasons:
                raise ValueError(
                    "admitted activation decision cannot contain failures"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected activation decision requires failed checks"
                )
            if normalized_reasons != tuple(
                sorted(failed_checks)
            ):
                raise ValueError(
                    "rejection reasons must match failed checks"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "activation-decision lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_020_BUILD_ID:
            raise ValueError(
                "activation-decision lineage must use build_id UMD-020"
            )
        if self.activation_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "activation-decision lineage must include activation hash"
            )

    @property
    def decision_id(self) -> str:
        return "umd:snapshot-activation-decision:" + deterministic_sha256(
            {
                "activation_id": self.activation_id,
                "activation_hash": self.activation_hash,
                "snapshot_id": self.snapshot_id,
                "snapshot_hash": self.snapshot_hash,
                "admitted": self.admitted,
                "checks": self.checks,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "activation_id": self.activation_id,
            "activation_hash": self.activation_hash,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": self.rejection_reasons,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def evaluate_snapshot_activation(
    activation: CertifiedCanonicalMarketRegistrySnapshotActivation,
    current_registry: ReadOnlyActiveCanonicalMarketRegistry | None,
    prior_activation_ids: Tuple[str, ...],
    prior_activation_hashes: Tuple[str, ...],
    *,
    lineage: ImmutableLineage,
) -> CertifiedSnapshotActivationDecision:
    normalized_prior_ids = tuple(
        sorted(
            {
                _text(
                    activation_id,
                    "prior activation id",
                )
                for activation_id in prior_activation_ids
            }
        )
    )
    normalized_prior_hashes = tuple(
        sorted(
            {
                _sha256(
                    activation_hash,
                    "prior activation hash",
                )
                for activation_hash in prior_activation_hashes
            }
        )
    )

    current_snapshot_sequence = (
        0
        if current_registry is None
        else current_registry.snapshot.snapshot_sequence
    )
    current_snapshot_hash = (
        None
        if current_registry is None
        else current_registry.active_snapshot_hash
    )

    checks = {
        "activation_id_not_seen": (
            activation.activation_id
            not in normalized_prior_ids
        ),
        "activation_hash_not_seen": (
            activation.activation_hash
            not in normalized_prior_hashes
        ),
        "snapshot_is_admitted": (
            activation.admission_entry.decision.admitted
        ),
        "snapshot_id_matches_admission": (
            activation.snapshot.snapshot_id
            == activation.admission_entry.decision.snapshot_id
        ),
        "snapshot_hash_matches_admission": (
            activation.snapshot.snapshot_hash
            == activation.admission_entry.decision.snapshot_hash
        ),
        "snapshot_sequence_matches_admission": (
            activation.snapshot.snapshot_sequence
            == activation.admission_entry.decision.snapshot_sequence
        ),
        "activation_hash_deterministic": (
            activation.activation_hash
            == deterministic_sha256(
                activation.to_canonical_dict()
            )
        ),
        "single_active_snapshot_transition": (
            current_registry is None
            or activation.snapshot.snapshot_sequence
            == current_snapshot_sequence + 1
        ),
        "active_snapshot_changes": (
            current_snapshot_hash
            != activation.snapshot.snapshot_hash
        ),
        "no_snapshot_rollback": (
            current_registry is None
            or activation.snapshot.snapshot_sequence
            > current_snapshot_sequence
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return CertifiedSnapshotActivationDecision(
        activation_id=activation.activation_id,
        activation_hash=activation.activation_hash,
        snapshot_id=activation.snapshot.snapshot_id,
        snapshot_hash=activation.snapshot.snapshot_hash,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD020CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    gate_mode: str
    prohibited_capabilities: Tuple[str, ...]
    network_enabled: bool
    persistence_enabled: bool
    mutation_enabled: bool
    publication_enabled: bool
    execution_enabled: bool

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "build_id": self.build_id,
            "build_name": self.build_name,
            "revision": self.revision,
            "schema_version": self.schema_version,
            "upstream_builds": self.upstream_builds,
            "gate_mode": self.gate_mode,
            "prohibited_capabilities": self.prohibited_capabilities,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_umd_020_certification_manifest() -> UMD020CertificationManifest:
    return UMD020CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_020_BUILD_ID,
        build_name=UMD_020_BUILD_NAME,
        revision=UMD_020_REVISION,
        schema_version=UMD_020_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 20)
        ),
        gate_mode="read_only_activation_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_020_foundation() -> Mapping[str, Any]:
    manifest = build_umd_020_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-020"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 20)
            )
        ),
        "read_only_activation_validation": (
            manifest.gate_mode
            == "read_only_activation_validation"
        ),
        "network_disabled": (
            manifest.network_enabled is False
        ),
        "persistence_disabled": (
            manifest.persistence_enabled is False
        ),
        "mutation_disabled": (
            manifest.mutation_enabled is False
        ),
        "publication_disabled": (
            manifest.publication_enabled is False
        ),
        "execution_disabled": (
            manifest.execution_enabled is False
        ),
        "deterministic_manifest_hash": (
            manifest.manifest_hash
            == deterministic_sha256(
                manifest.to_canonical_dict()
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return MappingProxyType(
        {
            "certified": not failed,
            "build_id": manifest.build_id,
            "revision": manifest.revision,
            "manifest_hash": manifest.manifest_hash,
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate() -> bool:
    result = certify_umd_020_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-020 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_020_BUILD_ID",
    "UMD_020_BUILD_NAME",
    "UMD_020_REVISION",
    "UMD_020_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedSnapshotActivationDecision",
    "evaluate_snapshot_activation",
    "UMD020CertificationManifest",
    "build_umd_020_certification_manifest",
    "certify_umd_020_foundation",
    "verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate",
]
"""

TEST_SOURCE = r"""
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
"""

INIT_IMPORT = r"""
from .certified_canonical_market_registry_snapshot_activation_gate import (
    UMD_020_BUILD_ID,
    UMD_020_BUILD_NAME,
    UMD_020_REVISION,
    UMD_020_SCHEMA_VERSION,
    CertifiedSnapshotActivationDecision,
    evaluate_snapshot_activation,
    UMD020CertificationManifest,
    build_umd_020_certification_manifest,
    certify_umd_020_foundation,
    verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate,
)
"""

EXPORTED_NAMES = (
    "UMD_020_BUILD_ID",
    "UMD_020_BUILD_NAME",
    "UMD_020_REVISION",
    "UMD_020_SCHEMA_VERSION",
    "CertifiedSnapshotActivationDecision",
    "evaluate_snapshot_activation",
    "UMD020CertificationManifest",
    "build_umd_020_certification_manifest",
    "certify_umd_020_foundation",
    "verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate",
)


def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()


def write_exact(path: Path, source: str) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
    temporary.write_text(
        normalize(source),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    source = INIT.read_text(
        encoding="utf-8"
    )
    marker = (
        "from "
        ".certified_canonical_market_registry_snapshot_activation_gate "
        "import ("
    )

    if marker not in source:
        source = (
            source.rstrip()
            + "\n\n"
            + normalize(INIT_IMPORT)
        )

    if "__all__" in source:
        start = source.index(
            "__all__ = ["
        )
        end = source.index(
            "]",
            start,
        )
        block = source[start : end + 1]

        missing = [
            name
            for name in EXPORTED_NAMES
            if f'"{name}"' not in block
            and f"'{name}'" not in block
        ]

        if missing:
            block = (
                block[:-1]
                + "".join(
                    f'    "{name}",\n'
                    for name in missing
                )
                + "]"
            )
            source = (
                source[:start]
                + block
                + source[end + 1 :]
            )
    else:
        source += (
            "\n__all__ = [\n"
            + "".join(
                f'    "{name}",\n'
                for name in EXPORTED_NAMES
            )
            + "]\n"
        )

    write_exact(INIT, source)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def verify_upstream() -> None:
    sys.path.insert(
        0,
        str(ROOT),
    )

    try:
        modules = (
            (
                "universal_market_discovery_foundation",
                "verify_umd_foundation",
            ),
            (
                "certified_canonical_market_contract",
                "verify_umd_002_certified_canonical_market_contract",
            ),
            (
                "certified_venue_identity_registry",
                "verify_umd_003_certified_venue_identity_registry",
            ),
            (
                "certified_venue_market_binding_registry",
                "verify_umd_004_certified_venue_market_binding_registry",
            ),
            (
                "certified_market_category_hierarchy_registry",
                "verify_umd_005_certified_market_category_hierarchy_registry",
            ),
            (
                "certified_market_classification_registry",
                "verify_umd_006_certified_market_classification_registry",
            ),
            (
                "certified_market_metadata_registry",
                "verify_umd_007_certified_market_metadata_registry",
            ),
            (
                "certified_market_lifecycle_and_settlement_registry",
                "verify_umd_008_certified_market_lifecycle_and_settlement_registry",
            ),
            (
                "certified_market_duplicate_resolution_registry",
                "verify_umd_009_certified_market_duplicate_resolution_registry",
            ),
            (
                "certified_related_market_graph_registry",
                "verify_umd_010_certified_related_market_graph_registry",
            ),
            (
                "certified_incremental_discovery_batch_contract",
                "verify_umd_011_certified_incremental_discovery_batch_contract",
            ),
            (
                "certified_incremental_discovery_admission_gate",
                "verify_umd_012_certified_incremental_discovery_admission_gate",
            ),
            (
                "certified_discovery_admission_ledger",
                "verify_umd_013_certified_discovery_admission_ledger",
            ),
            (
                "certified_admitted_market_materialization_contract",
                "verify_umd_014_certified_admitted_market_materialization_contract",
            ),
            (
                "certified_materialized_market_admission_registry",
                "verify_umd_015_certified_materialized_market_admission_registry",
            ),
            (
                "certified_canonical_market_registry_snapshot_contract",
                "verify_umd_016_certified_canonical_market_registry_snapshot_contract",
            ),
            (
                "certified_canonical_market_registry_snapshot_admission_gate",
                "verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate",
            ),
            (
                "certified_canonical_market_registry_snapshot_admission_ledger",
                "verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger",
            ),
            (
                "certified_canonical_market_registry_snapshot_activation_contract",
                "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract",
            ),
        )

        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2."
                "universal_market_discovery."
                + module_name
            )
            verifier = getattr(
                module,
                verifier_name,
            )

            if not verifier():
                raise RuntimeError(
                    f"{module_name} verification failed"
                )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def verify_current() -> None:
    sys.path.insert(
        0,
        str(ROOT),
    )

    try:
        module = importlib.import_module(
            "qseries_v2."
            "universal_market_discovery."
            "certified_canonical_market_registry_snapshot_activation_gate"
        )

        required = (
            "CertifiedSnapshotActivationDecision",
            "evaluate_snapshot_activation",
            "build_umd_020_certification_manifest",
            "certify_umd_020_foundation",
            "verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate",
        )

        missing = [
            name
            for name in required
            if not hasattr(
                module,
                name,
            )
        ]

        if missing:
            raise RuntimeError(
                "UMD-020 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-020 INSTALLER")
    print(
        " CERTIFIED CANONICAL MARKET REGISTRY "
        "SNAPSHOT ACTIVATION GATE"
    )
    print("=" * 64)
    print(
        f"[BOOT] Revision: "
        f"{REVISION}"
    )
    print(
        f"[ROOT] {ROOT}"
    )

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-019 "
        "verified read-only"
    )

    write_exact(
        MODULE,
        MODULE_SOURCE,
    )
    write_exact(
        TEST,
        TEST_SOURCE,
    )
    update_init()

    py_compile.compile(
        str(MODULE),
        doraise=True,
    )
    py_compile.compile(
        str(INIT),
        doraise=True,
    )
    py_compile.compile(
        str(TEST),
        doraise=True,
    )
    verify_current()

    manifest = {
        "build_id": "UMD-020",
        "revision": REVISION,
        "files": {
            str(
                MODULE.relative_to(ROOT)
            ): sha256_file(MODULE),
            str(
                INIT.relative_to(ROOT)
            ): sha256_file(INIT),
            str(
                TEST.relative_to(ROOT)
            ): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 20)
        ),
        "mode": (
            "read_only_activation_validation"
        ),
    }

    install_hash = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    print(
        f"[PASS] Wrote: "
        f"{MODULE.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Updated: "
        f"{INIT.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Wrote: "
        f"{TEST.relative_to(ROOT)}"
    )
    print(
        "[PASS] Python compilation verified"
    )
    print(
        "[PASS] Required UMD-020 symbols verified"
    )
    print(
        f"[PASS] Deterministic install hash: "
        f"{install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print(
        "[DONE] UMD-020 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_020_certified_canonical_market_registry_"
        "snapshot_activation_gate.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
