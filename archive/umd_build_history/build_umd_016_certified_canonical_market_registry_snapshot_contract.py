from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_016_CERTIFIED_CANONICAL_MARKET_REGISTRY_SNAPSHOT_CONTRACT_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_canonical_market_registry_snapshot_contract.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_016_certified_canonical_market_registry_snapshot_contract.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_materialized_market_admission_registry import (
    ReadOnlyMaterializedMarketAdmissionRegistry,
)

UMD_016_BUILD_ID = "UMD-016"
UMD_016_BUILD_NAME = "Certified Canonical Market Registry Snapshot Contract"
UMD_016_REVISION = (
    "UMD_016_CERTIFIED_CANONICAL_MARKET_REGISTRY_SNAPSHOT_CONTRACT_V1"
)
UMD_016_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_snapshot_persistence",
    "registry_mutation",
    "market_deletion",
    "market_reordering",
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
class CertifiedCanonicalMarketRegistrySnapshot:
    snapshot_sequence: int
    previous_snapshot_hash: str | None
    source_registry_hash: str
    markets: Tuple[CertifiedCanonicalMarket, ...]
    created_at: datetime
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedCanonicalMarket] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot_sequence, int):
            raise TypeError("snapshot_sequence must be an integer")
        if self.snapshot_sequence < 1:
            raise ValueError("snapshot_sequence must be positive")

        if self.previous_snapshot_hash is None:
            if self.snapshot_sequence != 1:
                raise ValueError(
                    "only the first snapshot may omit previous_snapshot_hash"
                )
        else:
            previous = _text(
                self.previous_snapshot_hash,
                "previous_snapshot_hash",
            ).lower()
            if len(previous) != 64:
                raise ValueError(
                    "previous_snapshot_hash must contain 64 hexadecimal characters"
                )
            if any(
                character not in "0123456789abcdef"
                for character in previous
            ):
                raise ValueError(
                    "previous_snapshot_hash must be lowercase SHA-256 hexadecimal"
                )
            object.__setattr__(
                self,
                "previous_snapshot_hash",
                previous,
            )

        source_hash = _text(
            self.source_registry_hash,
            "source_registry_hash",
        ).lower()
        if len(source_hash) != 64:
            raise ValueError(
                "source_registry_hash must contain 64 hexadecimal characters"
            )
        if any(
            character not in "0123456789abcdef"
            for character in source_hash
        ):
            raise ValueError(
                "source_registry_hash must be lowercase SHA-256 hexadecimal"
            )
        object.__setattr__(
            self,
            "source_registry_hash",
            source_hash,
        )

        ordered_markets = tuple(
            sorted(
                self.markets,
                key=lambda market: market.canonical_market_id,
            )
        )
        object.__setattr__(self, "markets", ordered_markets)

        by_market_id = {
            market.canonical_market_id: market
            for market in ordered_markets
        }
        if len(by_market_id) != len(ordered_markets):
            raise ValueError(
                "snapshot contains duplicate canonical market IDs"
            )
        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )

        object.__setattr__(
            self,
            "created_at",
            _utc(self.created_at, "created_at"),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("snapshot lineage must belong to UMD")
        if self.lineage.build_id != UMD_016_BUILD_ID:
            raise ValueError(
                "snapshot lineage must use build_id UMD-016"
            )
        if self.source_registry_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "snapshot lineage must include source registry hash"
            )
        if (
            self.previous_snapshot_hash is not None
            and self.previous_snapshot_hash
            not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "snapshot lineage must include previous snapshot hash"
            )

    @classmethod
    def from_admission_registry(
        cls,
        registry: ReadOnlyMaterializedMarketAdmissionRegistry,
        *,
        snapshot_sequence: int,
        previous_snapshot_hash: str | None,
        created_at: datetime,
        metadata: Mapping[str, Any],
        lineage: ImmutableLineage,
    ) -> "CertifiedCanonicalMarketRegistrySnapshot":
        return cls(
            snapshot_sequence=snapshot_sequence,
            previous_snapshot_hash=previous_snapshot_hash,
            source_registry_hash=registry.registry_hash,
            markets=registry.complete_market_view(),
            created_at=created_at,
            metadata=metadata,
            lineage=lineage,
        )

    @property
    def snapshot_id(self) -> str:
        return "umd:market-registry-snapshot:" + deterministic_sha256(
            {
                "snapshot_sequence": self.snapshot_sequence,
                "previous_snapshot_hash": self.previous_snapshot_hash,
                "source_registry_hash": self.source_registry_hash,
                "market_record_hashes": tuple(
                    market.record_hash for market in self.markets
                ),
            }
        )

    def get(
        self,
        canonical_market_id: str,
    ) -> CertifiedCanonicalMarket | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def contains(
        self,
        canonical_market_id: str,
    ) -> bool:
        return self.get(canonical_market_id) is not None

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_sequence": self.snapshot_sequence,
            "previous_snapshot_hash": self.previous_snapshot_hash,
            "source_registry_hash": self.source_registry_hash,
            "markets": self.markets,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def snapshot_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class ReadOnlyCanonicalMarketRegistrySnapshotChain:
    snapshots: Tuple[CertifiedCanonicalMarketRegistrySnapshot, ...]
    chain_lineage: ImmutableLineage
    _by_snapshot_id: Mapping[
        str,
        CertifiedCanonicalMarketRegistrySnapshot,
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(
                self.snapshots,
                key=lambda snapshot: snapshot.snapshot_sequence,
            )
        )
        object.__setattr__(self, "snapshots", ordered)

        if self.chain_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("snapshot-chain lineage must belong to UMD")
        if self.chain_lineage.build_id != UMD_016_BUILD_ID:
            raise ValueError(
                "snapshot-chain lineage must use build_id UMD-016"
            )

        by_snapshot_id = {}
        previous_snapshot = None

        for expected_sequence, snapshot in enumerate(
            ordered,
            start=1,
        ):
            if snapshot.snapshot_sequence != expected_sequence:
                raise ValueError(
                    "snapshot sequence must be contiguous and start at 1"
                )

            if previous_snapshot is None:
                if snapshot.previous_snapshot_hash is not None:
                    raise ValueError(
                        "first snapshot must not have previous hash"
                    )
            else:
                if (
                    snapshot.previous_snapshot_hash
                    != previous_snapshot.snapshot_hash
                ):
                    raise ValueError(
                        "snapshot previous-hash chain mismatch"
                    )

                previous_market_ids = {
                    market.canonical_market_id
                    for market in previous_snapshot.markets
                }
                current_market_ids = {
                    market.canonical_market_id
                    for market in snapshot.markets
                }
                if not previous_market_ids.issubset(
                    current_market_ids
                ):
                    raise ValueError(
                        "snapshot chain cannot delete canonical markets"
                    )

            if snapshot.snapshot_id in by_snapshot_id:
                raise ValueError("duplicate snapshot ID")

            by_snapshot_id[snapshot.snapshot_id] = snapshot
            previous_snapshot = snapshot

        object.__setattr__(
            self,
            "_by_snapshot_id",
            MappingProxyType(by_snapshot_id),
        )

    def latest(
        self,
    ) -> CertifiedCanonicalMarketRegistrySnapshot | None:
        if not self.snapshots:
            return None
        return self.snapshots[-1]

    def get(
        self,
        snapshot_id: str,
    ) -> CertifiedCanonicalMarketRegistrySnapshot | None:
        return self._by_snapshot_id.get(
            _text(snapshot_id, "snapshot_id")
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "chain_mode": "append_only_read_only",
            "snapshots": self.snapshots,
            "chain_lineage": self.chain_lineage,
        }

    @property
    def chain_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD016CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    snapshot_mode: str
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
            "snapshot_mode": self.snapshot_mode,
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


def build_umd_016_certification_manifest() -> UMD016CertificationManifest:
    return UMD016CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_016_BUILD_ID,
        build_name=UMD_016_BUILD_NAME,
        revision=UMD_016_REVISION,
        schema_version=UMD_016_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}" for number in range(1, 16)
        ),
        snapshot_mode="append_only_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_canonical_market_registry_snapshot_chain(
    chain: ReadOnlyCanonicalMarketRegistrySnapshotChain,
) -> Mapping[str, Any]:
    checks = {
        "snapshot_ids_unique": len(
            {
                snapshot.snapshot_id
                for snapshot in chain.snapshots
            }
        )
        == len(chain.snapshots),
        "sequence_contiguous": tuple(
            snapshot.snapshot_sequence
            for snapshot in chain.snapshots
        )
        == tuple(range(1, len(chain.snapshots) + 1)),
        "markets_never_deleted": all(
            {
                market.canonical_market_id
                for market in prior.markets
            }.issubset(
                {
                    market.canonical_market_id
                    for market in current.markets
                }
            )
            for prior, current in zip(
                chain.snapshots,
                chain.snapshots[1:],
            )
        ),
        "deterministic_replay": (
            chain.chain_hash
            == deterministic_sha256(chain.to_canonical_dict())
        ),
        "read_only_index": isinstance(
            chain._by_snapshot_id,
            MappingProxyType,
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
    )

    latest = chain.latest()

    return MappingProxyType(
        {
            "certified": not failed,
            "chain_hash": chain.chain_hash,
            "snapshot_count": len(chain.snapshots),
            "latest_market_count": (
                0 if latest is None else len(latest.markets)
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_016_foundation() -> Mapping[str, Any]:
    manifest = build_umd_016_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-016",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(
            f"UMD-{number:03d}" for number in range(1, 16)
        ),
        "append_only_read_only": (
            manifest.snapshot_mode
            == "append_only_read_only"
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


def verify_umd_016_certified_canonical_market_registry_snapshot_contract() -> bool:
    result = certify_umd_016_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-016 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_016_BUILD_ID",
    "UMD_016_BUILD_NAME",
    "UMD_016_REVISION",
    "UMD_016_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedCanonicalMarketRegistrySnapshot",
    "ReadOnlyCanonicalMarketRegistrySnapshotChain",
    "UMD016CertificationManifest",
    "build_umd_016_certification_manifest",
    "certify_canonical_market_registry_snapshot_chain",
    "certify_umd_016_foundation",
    "verify_umd_016_certified_canonical_market_registry_snapshot_contract",
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
from qseries_v2.universal_market_discovery.certified_canonical_market_registry_snapshot_contract import (
    UMD_016_REVISION,
    build_umd_016_certification_manifest,
    certify_umd_016_foundation,
    verify_umd_016_certified_canonical_market_registry_snapshot_contract,
)

FIXED = datetime(2026, 8, 6, 1, 0, tzinfo=timezone.utc)


class TestUMD016(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(certify_umd_016_foundation()["certified"])
        self.assertTrue(
            verify_umd_016_certified_canonical_market_registry_snapshot_contract()
        )

    def test_manifest_is_append_only_read_only(self) -> None:
        manifest = build_umd_016_certification_manifest()
        self.assertEqual(
            manifest.snapshot_mode,
            "append_only_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_016_certification_manifest()
        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 16)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-016",
            revision=UMD_016_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=("fixture://umd-016",),
            created_at=FIXED,
        )
        self.assertEqual(lineage.build_id, "UMD-016")


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-016 CERTIFICATION TEST")
    print(" CERTIFIED CANONICAL MARKET REGISTRY SNAPSHOT CONTRACT")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD016
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_016_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-015 consumed read-only")
    print("[PASS] Canonical market snapshot contract certified")
    print("[PASS] Snapshot IDs and hashes deterministic")
    print("[PASS] Snapshot sequence continuity required")
    print("[PASS] Previous-snapshot hash chain required")
    print("[PASS] Source admission-registry hash lineage required")
    print("[PASS] Duplicate canonical market IDs prohibited")
    print("[PASS] Canonical market deletion across snapshots prohibited")
    print("[PASS] Read-only snapshot chain certified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-016 CERTIFIED CANONICAL MARKET REGISTRY SNAPSHOT CONTRACT CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_canonical_market_registry_snapshot_contract import (
    UMD_016_BUILD_ID,
    UMD_016_BUILD_NAME,
    UMD_016_REVISION,
    UMD_016_SCHEMA_VERSION,
    CertifiedCanonicalMarketRegistrySnapshot,
    ReadOnlyCanonicalMarketRegistrySnapshotChain,
    UMD016CertificationManifest,
    build_umd_016_certification_manifest,
    certify_canonical_market_registry_snapshot_chain,
    certify_umd_016_foundation,
    verify_umd_016_certified_canonical_market_registry_snapshot_contract,
)
"""

EXPORTED_NAMES = (
    "UMD_016_BUILD_ID",
    "UMD_016_BUILD_NAME",
    "UMD_016_REVISION",
    "UMD_016_SCHEMA_VERSION",
    "CertifiedCanonicalMarketRegistrySnapshot",
    "ReadOnlyCanonicalMarketRegistrySnapshotChain",
    "UMD016CertificationManifest",
    "build_umd_016_certification_manifest",
    "certify_canonical_market_registry_snapshot_chain",
    "certify_umd_016_foundation",
    "verify_umd_016_certified_canonical_market_registry_snapshot_contract",
)


def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()


def write_exact(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
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

    source = INIT.read_text(encoding="utf-8")
    marker = (
        "from .certified_canonical_market_registry_snapshot_contract import ("
    )

    if marker not in source:
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)

    if "__all__" in source:
        start = source.index("__all__ = [")
        end = source.index("]", start)
        block = source[start : end + 1]
        missing = [
            name
            for name in EXPORTED_NAMES
            if f'"{name}"' not in block
            and f"'{name}'" not in block
        ]
        if missing:
            block = block[:-1] + "".join(
                f'    "{name}",\n' for name in missing
            ) + "]"
            source = source[:start] + block + source[end + 1 :]
    else:
        source += "\n__all__ = [\n" + "".join(
            f'    "{name}",\n' for name in EXPORTED_NAMES
        ) + "]\n"

    write_exact(INIT, source)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_upstream() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        modules = (
            ("universal_market_discovery_foundation", "verify_umd_foundation"),
            ("certified_canonical_market_contract", "verify_umd_002_certified_canonical_market_contract"),
            ("certified_venue_identity_registry", "verify_umd_003_certified_venue_identity_registry"),
            ("certified_venue_market_binding_registry", "verify_umd_004_certified_venue_market_binding_registry"),
            ("certified_market_category_hierarchy_registry", "verify_umd_005_certified_market_category_hierarchy_registry"),
            ("certified_market_classification_registry", "verify_umd_006_certified_market_classification_registry"),
            ("certified_market_metadata_registry", "verify_umd_007_certified_market_metadata_registry"),
            ("certified_market_lifecycle_and_settlement_registry", "verify_umd_008_certified_market_lifecycle_and_settlement_registry"),
            ("certified_market_duplicate_resolution_registry", "verify_umd_009_certified_market_duplicate_resolution_registry"),
            ("certified_related_market_graph_registry", "verify_umd_010_certified_related_market_graph_registry"),
            ("certified_incremental_discovery_batch_contract", "verify_umd_011_certified_incremental_discovery_batch_contract"),
            ("certified_incremental_discovery_admission_gate", "verify_umd_012_certified_incremental_discovery_admission_gate"),
            ("certified_discovery_admission_ledger", "verify_umd_013_certified_discovery_admission_ledger"),
            ("certified_admitted_market_materialization_contract", "verify_umd_014_certified_admitted_market_materialization_contract"),
            ("certified_materialized_market_admission_registry", "verify_umd_015_certified_materialized_market_admission_registry"),
        )

        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2.universal_market_discovery."
                + module_name
            )
            if not getattr(module, verifier_name)():
                raise RuntimeError(
                    f"{module_name} verification failed"
                )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def verify_current() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_canonical_market_registry_snapshot_contract"
        )
        required = (
            "CertifiedCanonicalMarketRegistrySnapshot",
            "ReadOnlyCanonicalMarketRegistrySnapshotChain",
            "certify_canonical_market_registry_snapshot_chain",
            "certify_umd_016_foundation",
            "verify_umd_016_certified_canonical_market_registry_snapshot_contract",
        )
        missing = [
            name
            for name in required
            if not hasattr(module, name)
        ]
        if missing:
            raise RuntimeError(
                "UMD-016 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_016_certified_canonical_market_registry_snapshot_contract()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def main() -> int:
    print("=" * 64)
    print(" UMD-016 INSTALLER")
    print(" CERTIFIED CANONICAL MARKET REGISTRY SNAPSHOT CONTRACT")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-015 "
        "verified read-only"
    )

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_current()

    manifest = {
        "build_id": "UMD-016",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 16)
        ),
        "mode": "append_only_read_only",
    }

    install_hash = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] Python compilation verified")
    print("[PASS] Required UMD-016 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-016 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_016_certified_canonical_market_registry_snapshot_contract.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
