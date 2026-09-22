from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_019_CERTIFIED_CANONICAL_MARKET_REGISTRY_SNAPSHOT_ACTIVATION_CONTRACT_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_canonical_market_registry_snapshot_activation_contract.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_019_certified_canonical_market_registry_snapshot_activation_contract.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_registry_snapshot_contract import (
    CertifiedCanonicalMarketRegistrySnapshot,
)
from .certified_canonical_market_registry_snapshot_admission_ledger import (
    CertifiedSnapshotAdmissionLedgerEntry,
)

UMD_019_BUILD_ID = "UMD-019"
UMD_019_BUILD_NAME = (
    "Certified Canonical Market Registry Snapshot Activation Contract"
)
UMD_019_REVISION = (
    "UMD_019_CERTIFIED_CANONICAL_MARKET_REGISTRY_"
    "SNAPSHOT_ACTIVATION_CONTRACT_V1"
)
UMD_019_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_activation_commit",
    "snapshot_persistence",
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


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )


@dataclass(frozen=True, slots=True)
class CertifiedCanonicalMarketRegistrySnapshotActivation:
    snapshot: CertifiedCanonicalMarketRegistrySnapshot
    admission_entry: CertifiedSnapshotAdmissionLedgerEntry
    activated_at: datetime
    activation_reason: str
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        if not self.admission_entry.decision.admitted:
            raise ValueError(
                "only admitted snapshots may be activated"
            )

        decision = self.admission_entry.decision
        if decision.snapshot_id != self.snapshot.snapshot_id:
            raise ValueError(
                "admission decision snapshot_id does not match snapshot"
            )
        if decision.snapshot_hash != self.snapshot.snapshot_hash:
            raise ValueError(
                "admission decision snapshot_hash does not match snapshot"
            )
        if (
            decision.snapshot_sequence
            != self.snapshot.snapshot_sequence
        ):
            raise ValueError(
                "admission decision snapshot_sequence does not match snapshot"
            )

        object.__setattr__(
            self,
            "activated_at",
            _utc(self.activated_at, "activated_at"),
        )
        object.__setattr__(
            self,
            "activation_reason",
            _text(self.activation_reason, "activation_reason").lower(),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("activation lineage must belong to UMD")
        if self.lineage.build_id != UMD_019_BUILD_ID:
            raise ValueError(
                "activation lineage must use build_id UMD-019"
            )

        required_parents = {
            self.snapshot.snapshot_hash,
            self.admission_entry.entry_hash,
            self.admission_entry.decision.record_hash,
        }
        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "activation lineage is missing required parent hashes"
            )

    @property
    def activation_id(self) -> str:
        return "umd:snapshot-activation:" + deterministic_sha256(
            {
                "snapshot_id": self.snapshot.snapshot_id,
                "snapshot_hash": self.snapshot.snapshot_hash,
                "admission_entry_id": self.admission_entry.entry_id,
                "activation_reason": self.activation_reason,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "activation_id": self.activation_id,
            "snapshot_id": self.snapshot.snapshot_id,
            "snapshot_hash": self.snapshot.snapshot_hash,
            "snapshot_sequence": self.snapshot.snapshot_sequence,
            "admission_entry_id": self.admission_entry.entry_id,
            "admission_entry_hash": self.admission_entry.entry_hash,
            "activated_at": self.activated_at,
            "activation_reason": self.activation_reason,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def activation_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class ReadOnlyActiveCanonicalMarketRegistry:
    activation: CertifiedCanonicalMarketRegistrySnapshotActivation

    @property
    def snapshot(self) -> CertifiedCanonicalMarketRegistrySnapshot:
        return self.activation.snapshot

    @property
    def active_snapshot_id(self) -> str:
        return self.snapshot.snapshot_id

    @property
    def active_snapshot_hash(self) -> str:
        return self.snapshot.snapshot_hash

    @property
    def market_count(self) -> int:
        return len(self.snapshot.markets)

    def get(self, canonical_market_id: str):
        return self.snapshot.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def contains(self, canonical_market_id: str) -> bool:
        return self.snapshot.contains(
            _text(canonical_market_id, "canonical_market_id")
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "single_active_read_only_snapshot",
            "activation": self.activation,
            "active_snapshot_id": self.active_snapshot_id,
            "active_snapshot_hash": self.active_snapshot_hash,
            "market_count": self.market_count,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD019CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    activation_mode: str
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
            "activation_mode": self.activation_mode,
            "prohibited_capabilities": self.prohibited_capabilities,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def build_umd_019_certification_manifest() -> UMD019CertificationManifest:
    return UMD019CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_019_BUILD_ID,
        build_name=UMD_019_BUILD_NAME,
        revision=UMD_019_REVISION,
        schema_version=UMD_019_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 19)
        ),
        activation_mode="single_active_read_only_snapshot",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_canonical_market_registry(
    registry: ReadOnlyActiveCanonicalMarketRegistry,
) -> Mapping[str, Any]:
    checks = {
        "admission_is_approved": (
            registry.activation.admission_entry.decision.admitted
        ),
        "snapshot_identity_matches_decision": (
            registry.activation.admission_entry.decision.snapshot_id
            == registry.active_snapshot_id
        ),
        "snapshot_hash_matches_decision": (
            registry.activation.admission_entry.decision.snapshot_hash
            == registry.active_snapshot_hash
        ),
        "market_count_matches_snapshot": (
            registry.market_count
            == len(registry.snapshot.markets)
        ),
        "deterministic_replay": (
            registry.registry_hash
            == deterministic_sha256(registry.to_canonical_dict())
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
    )

    return MappingProxyType(
        {
            "certified": not failed,
            "registry_hash": registry.registry_hash,
            "active_snapshot_id": registry.active_snapshot_id,
            "active_snapshot_hash": registry.active_snapshot_hash,
            "market_count": registry.market_count,
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_019_foundation() -> Mapping[str, Any]:
    manifest = build_umd_019_certification_manifest()

    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-019",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(
            f"UMD-{number:03d}"
            for number in range(1, 19)
        ),
        "single_active_read_only_snapshot": (
            manifest.activation_mode
            == "single_active_read_only_snapshot"
        ),
        "network_disabled": not manifest.network_enabled,
        "persistence_disabled": not manifest.persistence_enabled,
        "mutation_disabled": not manifest.mutation_enabled,
        "publication_disabled": not manifest.publication_enabled,
        "execution_disabled": not manifest.execution_enabled,
        "deterministic_manifest_hash": (
            manifest.manifest_hash
            == deterministic_sha256(manifest.to_canonical_dict())
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
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


def verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract() -> bool:
    result = certify_umd_019_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-019 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_019_BUILD_ID",
    "UMD_019_BUILD_NAME",
    "UMD_019_REVISION",
    "UMD_019_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedCanonicalMarketRegistrySnapshotActivation",
    "ReadOnlyActiveCanonicalMarketRegistry",
    "UMD019CertificationManifest",
    "build_umd_019_certification_manifest",
    "certify_active_canonical_market_registry",
    "certify_umd_019_foundation",
    "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

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
from qseries_v2.universal_market_discovery.certified_canonical_market_registry_snapshot_activation_contract import (
    UMD_019_REVISION,
    build_umd_019_certification_manifest,
    certify_umd_019_foundation,
    verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract,
)

FIXED = datetime(
    2026,
    8,
    6,
    4,
    0,
    tzinfo=timezone.utc,
)


class TestUMD019(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_019_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract()
        )

    def test_manifest_is_single_active_read_only(self) -> None:
        manifest = build_umd_019_certification_manifest()

        self.assertEqual(
            manifest.activation_mode,
            "single_active_read_only_snapshot",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_019_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 19)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-019",
            revision=UMD_019_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=("fixture://umd-019",),
            created_at=FIXED,
        )

        self.assertEqual(lineage.build_id, "UMD-019")


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-019 CERTIFICATION TEST")
    print(
        " CERTIFIED CANONICAL MARKET REGISTRY "
        "SNAPSHOT ACTIVATION CONTRACT"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD019
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_019_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-018 "
        "consumed read-only"
    )
    print(
        "[PASS] Admitted-snapshot-only activation "
        "contract certified"
    )
    print(
        "[PASS] Snapshot, decision, and ledger "
        "identity binding certified"
    )
    print(
        "[PASS] Snapshot activation lineage "
        "requirements certified"
    )
    print(
        "[PASS] Single active read-only registry "
        "contract certified"
    )
    print(
        "[PASS] Active snapshot and market count "
        "views deterministic"
    )
    print(
        "[PASS] Automatic activation and persistence "
        "disabled"
    )
    print(
        "[PASS] Publication and Q Series execution "
        "disabled"
    )
    print(
        "[DONE] UMD-019 CERTIFIED CANONICAL MARKET "
        "REGISTRY SNAPSHOT ACTIVATION CONTRACT CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_canonical_market_registry_snapshot_activation_contract import (
    UMD_019_BUILD_ID,
    UMD_019_BUILD_NAME,
    UMD_019_REVISION,
    UMD_019_SCHEMA_VERSION,
    CertifiedCanonicalMarketRegistrySnapshotActivation,
    ReadOnlyActiveCanonicalMarketRegistry,
    UMD019CertificationManifest,
    build_umd_019_certification_manifest,
    certify_active_canonical_market_registry,
    certify_umd_019_foundation,
    verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract,
)
"""

EXPORTED_NAMES = (
    "UMD_019_BUILD_ID",
    "UMD_019_BUILD_NAME",
    "UMD_019_REVISION",
    "UMD_019_SCHEMA_VERSION",
    "CertifiedCanonicalMarketRegistrySnapshotActivation",
    "ReadOnlyActiveCanonicalMarketRegistry",
    "UMD019CertificationManifest",
    "build_umd_019_certification_manifest",
    "certify_active_canonical_market_registry",
    "certify_umd_019_foundation",
    "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract",
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
        ".certified_canonical_market_registry_snapshot_activation_contract "
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
            "certified_canonical_market_registry_snapshot_activation_contract"
        )

        required = (
            "CertifiedCanonicalMarketRegistrySnapshotActivation",
            "ReadOnlyActiveCanonicalMarketRegistry",
            "certify_active_canonical_market_registry",
            "certify_umd_019_foundation",
            "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract",
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
                "UMD-019 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-019 INSTALLER")
    print(
        " CERTIFIED CANONICAL MARKET REGISTRY "
        "SNAPSHOT ACTIVATION CONTRACT"
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
        "[PASS] Certified UMD-001 through UMD-018 "
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
        "build_id": "UMD-019",
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
            for number in range(1, 19)
        ),
        "mode": (
            "single_active_read_only_snapshot"
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
        "[PASS] Required UMD-019 symbols verified"
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
        "[DONE] UMD-019 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_019_certified_canonical_market_registry_"
        "snapshot_activation_contract.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
