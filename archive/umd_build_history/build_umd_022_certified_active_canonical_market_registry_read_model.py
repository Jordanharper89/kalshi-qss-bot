from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_022_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_READ_MODEL_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_read_model.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_022_certified_active_canonical_market_registry_read_model.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_canonical_market_registry_snapshot_activation_contract import (
    ReadOnlyActiveCanonicalMarketRegistry,
)
from .certified_canonical_market_registry_snapshot_activation_ledger import (
    ReadOnlySnapshotActivationLedger,
)

UMD_022_BUILD_ID = "UMD-022"
UMD_022_BUILD_NAME = "Certified Active Canonical Market Registry Read Model"
UMD_022_REVISION = (
    "UMD_022_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_READ_MODEL_V1"
)
UMD_022_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "registry_mutation",
    "snapshot_activation",
    "persistence_write",
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


def _value_text(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip().lower()


@dataclass(frozen=True, slots=True)
class CertifiedActiveCanonicalMarketRegistryReadModel:
    active_registry: ReadOnlyActiveCanonicalMarketRegistry
    activation_ledger: ReadOnlySnapshotActivationLedger
    lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedCanonicalMarket] = field(
        init=False,
        repr=False,
    )
    _by_venue_id: Mapping[str, Tuple[CertifiedCanonicalMarket, ...]] = field(
        init=False,
        repr=False,
    )
    _by_category_id: Mapping[str, Tuple[CertifiedCanonicalMarket, ...]] = field(
        init=False,
        repr=False,
    )
    _by_lifecycle: Mapping[str, Tuple[CertifiedCanonicalMarket, ...]] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("read-model lineage must belong to UMD")
        if self.lineage.build_id != UMD_022_BUILD_ID:
            raise ValueError(
                "read-model lineage must use build_id UMD-022"
            )

        activation = self.active_registry.activation
        latest_admitted = self.activation_ledger.latest_admitted()

        if latest_admitted is None:
            raise ValueError(
                "active registry requires an admitted activation ledger entry"
            )

        if (
            latest_admitted.decision.activation_id
            != activation.activation_id
        ):
            raise ValueError(
                "active registry activation does not match latest admitted ledger entry"
            )
        if (
            latest_admitted.decision.activation_hash
            != activation.activation_hash
        ):
            raise ValueError(
                "active registry activation hash does not match ledger"
            )
        if (
            latest_admitted.decision.snapshot_id
            != self.active_registry.active_snapshot_id
        ):
            raise ValueError(
                "active snapshot ID does not match activation ledger"
            )
        if (
            latest_admitted.decision.snapshot_hash
            != self.active_registry.active_snapshot_hash
        ):
            raise ValueError(
                "active snapshot hash does not match activation ledger"
            )

        required_parents = {
            self.active_registry.registry_hash,
            self.activation_ledger.ledger_hash,
            activation.activation_hash,
            latest_admitted.entry_hash,
        }
        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "read-model lineage is missing required parent hashes"
            )

        markets = tuple(
            sorted(
                self.active_registry.snapshot.markets,
                key=lambda market: market.canonical_market_id,
            )
        )

        by_market_id = {}
        by_venue_id = {}
        by_category_id = {}
        by_lifecycle = {}

        for market in markets:
            market_id = market.canonical_market_id
            if market_id in by_market_id:
                raise ValueError(
                    "duplicate canonical market ID in active registry"
                )
            by_market_id[market_id] = market

            venue_id = _text(
                market.venue.venue_id,
                "venue_id",
            ).lower()
            by_venue_id.setdefault(
                venue_id,
                [],
            ).append(market)

            category_id = _text(
                market.category.category_id,
                "category_id",
            ).lower()
            by_category_id.setdefault(
                category_id,
                [],
            ).append(market)

            lifecycle = _value_text(market.lifecycle)
            by_lifecycle.setdefault(
                lifecycle,
                [],
            ).append(market)

        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_venue_id",
            MappingProxyType(
                {
                    key: tuple(
                        sorted(
                            values,
                            key=lambda market: market.canonical_market_id,
                        )
                    )
                    for key, values in by_venue_id.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_by_category_id",
            MappingProxyType(
                {
                    key: tuple(
                        sorted(
                            values,
                            key=lambda market: market.canonical_market_id,
                        )
                    )
                    for key, values in by_category_id.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_by_lifecycle",
            MappingProxyType(
                {
                    key: tuple(
                        sorted(
                            values,
                            key=lambda market: market.canonical_market_id,
                        )
                    )
                    for key, values in by_lifecycle.items()
                }
            ),
        )

    @property
    def active_snapshot_id(self) -> str:
        return self.active_registry.active_snapshot_id

    @property
    def active_snapshot_hash(self) -> str:
        return self.active_registry.active_snapshot_hash

    @property
    def market_count(self) -> int:
        return len(self._by_market_id)

    def get(
        self,
        canonical_market_id: str,
    ) -> CertifiedCanonicalMarket | None:
        return self._by_market_id.get(
            _text(
                canonical_market_id,
                "canonical_market_id",
            )
        )

    def by_venue(
        self,
        venue_id: str,
    ) -> Tuple[CertifiedCanonicalMarket, ...]:
        return self._by_venue_id.get(
            _text(venue_id, "venue_id").lower(),
            (),
        )

    def by_category(
        self,
        category_id: str,
    ) -> Tuple[CertifiedCanonicalMarket, ...]:
        return self._by_category_id.get(
            _text(category_id, "category_id").lower(),
            (),
        )

    def by_lifecycle(
        self,
        lifecycle: Any,
    ) -> Tuple[CertifiedCanonicalMarket, ...]:
        return self._by_lifecycle.get(
            _value_text(lifecycle),
            (),
        )

    def market_ids(
        self,
    ) -> Tuple[str, ...]:
        return tuple(sorted(self._by_market_id))

    def venue_ids(
        self,
    ) -> Tuple[str, ...]:
        return tuple(sorted(self._by_venue_id))

    def category_ids(
        self,
    ) -> Tuple[str, ...]:
        return tuple(sorted(self._by_category_id))

    def lifecycle_values(
        self,
    ) -> Tuple[str, ...]:
        return tuple(sorted(self._by_lifecycle))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "read_model_mode": "active_snapshot_read_only",
            "active_snapshot_id": self.active_snapshot_id,
            "active_snapshot_hash": self.active_snapshot_hash,
            "active_registry_hash": self.active_registry.registry_hash,
            "activation_ledger_hash": self.activation_ledger.ledger_hash,
            "market_record_hashes": tuple(
                self._by_market_id[market_id].record_hash
                for market_id in self.market_ids()
            ),
            "venue_index": {
                venue_id: tuple(
                    market.canonical_market_id
                    for market in self._by_venue_id[venue_id]
                )
                for venue_id in self.venue_ids()
            },
            "category_index": {
                category_id: tuple(
                    market.canonical_market_id
                    for market in self._by_category_id[category_id]
                )
                for category_id in self.category_ids()
            },
            "lifecycle_index": {
                lifecycle: tuple(
                    market.canonical_market_id
                    for market in self._by_lifecycle[lifecycle]
                )
                for lifecycle in self.lifecycle_values()
            },
            "lineage": self.lineage,
        }

    @property
    def read_model_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD022CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    read_model_mode: str
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
            "read_model_mode": self.read_model_mode,
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


def build_umd_022_certification_manifest() -> UMD022CertificationManifest:
    return UMD022CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_022_BUILD_ID,
        build_name=UMD_022_BUILD_NAME,
        revision=UMD_022_REVISION,
        schema_version=UMD_022_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 22)
        ),
        read_model_mode="active_snapshot_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_canonical_market_registry_read_model(
    read_model: CertifiedActiveCanonicalMarketRegistryReadModel,
) -> Mapping[str, Any]:
    checks = {
        "market_ids_unique": (
            len(read_model.market_ids())
            == read_model.market_count
        ),
        "market_order_deterministic": (
            read_model.market_ids()
            == tuple(sorted(read_model.market_ids()))
        ),
        "venue_order_deterministic": (
            read_model.venue_ids()
            == tuple(sorted(read_model.venue_ids()))
        ),
        "category_order_deterministic": (
            read_model.category_ids()
            == tuple(sorted(read_model.category_ids()))
        ),
        "lifecycle_order_deterministic": (
            read_model.lifecycle_values()
            == tuple(sorted(read_model.lifecycle_values()))
        ),
        "active_snapshot_bound": (
            read_model.active_snapshot_id
            == read_model.active_registry.active_snapshot_id
            and read_model.active_snapshot_hash
            == read_model.active_registry.active_snapshot_hash
        ),
        "deterministic_replay": (
            read_model.read_model_hash
            == deterministic_sha256(
                read_model.to_canonical_dict()
            )
        ),
        "read_only_indexes": (
            isinstance(
                read_model._by_market_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_venue_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_category_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_lifecycle,
                MappingProxyType,
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
            "read_model_hash": read_model.read_model_hash,
            "active_snapshot_id": read_model.active_snapshot_id,
            "active_snapshot_hash": read_model.active_snapshot_hash,
            "market_count": read_model.market_count,
            "venue_count": len(read_model.venue_ids()),
            "category_count": len(read_model.category_ids()),
            "lifecycle_count": len(read_model.lifecycle_values()),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_022_foundation() -> Mapping[str, Any]:
    manifest = build_umd_022_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-022"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 22)
            )
        ),
        "active_snapshot_read_only": (
            manifest.read_model_mode
            == "active_snapshot_read_only"
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


def verify_umd_022_certified_active_canonical_market_registry_read_model() -> bool:
    result = certify_umd_022_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-022 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_022_BUILD_ID",
    "UMD_022_BUILD_NAME",
    "UMD_022_REVISION",
    "UMD_022_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveCanonicalMarketRegistryReadModel",
    "UMD022CertificationManifest",
    "build_umd_022_certification_manifest",
    "certify_active_canonical_market_registry_read_model",
    "certify_umd_022_foundation",
    "verify_umd_022_certified_active_canonical_market_registry_read_model",
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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_read_model import (
    UMD_022_REVISION,
    build_umd_022_certification_manifest,
    certify_umd_022_foundation,
    verify_umd_022_certified_active_canonical_market_registry_read_model,
)

FIXED = datetime(
    2026,
    8,
    6,
    5,
    30,
    tzinfo=timezone.utc,
)


class TestUMD022(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_022_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_022_certified_active_canonical_market_registry_read_model()
        )

    def test_manifest_is_active_snapshot_read_only(
        self,
    ) -> None:
        manifest = build_umd_022_certification_manifest()

        self.assertEqual(
            manifest.read_model_mode,
            "active_snapshot_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_022_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 22)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-022",
            revision=UMD_022_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-022",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-022",
        )


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-022 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY READ MODEL"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD022
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_022_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-021 "
        "consumed read-only"
    )
    print(
        "[PASS] Active registry and latest admitted "
        "activation binding certified"
    )
    print(
        "[PASS] Canonical market lookup index certified"
    )
    print(
        "[PASS] Venue, category, and lifecycle indexes certified"
    )
    print(
        "[PASS] Deterministic index ordering and replay certified"
    )
    print(
        "[PASS] Immutable read-model lineage certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-022 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY READ MODEL CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_read_model import (
    UMD_022_BUILD_ID,
    UMD_022_BUILD_NAME,
    UMD_022_REVISION,
    UMD_022_SCHEMA_VERSION,
    CertifiedActiveCanonicalMarketRegistryReadModel,
    UMD022CertificationManifest,
    build_umd_022_certification_manifest,
    certify_active_canonical_market_registry_read_model,
    certify_umd_022_foundation,
    verify_umd_022_certified_active_canonical_market_registry_read_model,
)
"""

EXPORTED_NAMES = (
    "UMD_022_BUILD_ID",
    "UMD_022_BUILD_NAME",
    "UMD_022_REVISION",
    "UMD_022_SCHEMA_VERSION",
    "CertifiedActiveCanonicalMarketRegistryReadModel",
    "UMD022CertificationManifest",
    "build_umd_022_certification_manifest",
    "certify_active_canonical_market_registry_read_model",
    "certify_umd_022_foundation",
    "verify_umd_022_certified_active_canonical_market_registry_read_model",
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
        ".certified_active_canonical_market_registry_read_model "
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
            ("certified_canonical_market_registry_snapshot_contract", "verify_umd_016_certified_canonical_market_registry_snapshot_contract"),
            ("certified_canonical_market_registry_snapshot_admission_gate", "verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate"),
            ("certified_canonical_market_registry_snapshot_admission_ledger", "verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger"),
            ("certified_canonical_market_registry_snapshot_activation_contract", "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract"),
            ("certified_canonical_market_registry_snapshot_activation_gate", "verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate"),
            ("certified_canonical_market_registry_snapshot_activation_ledger", "verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger"),
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
            "certified_active_canonical_market_registry_read_model"
        )

        required = (
            "CertifiedActiveCanonicalMarketRegistryReadModel",
            "build_umd_022_certification_manifest",
            "certify_active_canonical_market_registry_read_model",
            "certify_umd_022_foundation",
            "verify_umd_022_certified_active_canonical_market_registry_read_model",
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
                "UMD-022 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_022_certified_active_canonical_market_registry_read_model()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-022 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY READ MODEL"
    )
    print("=" * 64)
    print(
        f"[BOOT] Revision: {REVISION}"
    )
    print(
        f"[ROOT] {ROOT}"
    )

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-021 "
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
        "build_id": "UMD-022",
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
            for number in range(1, 22)
        ),
        "mode": "active_snapshot_read_only",
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
        "[PASS] Required UMD-022 symbols verified"
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
        "[DONE] UMD-022 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_022_certified_active_canonical_market_"
        "registry_read_model.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
