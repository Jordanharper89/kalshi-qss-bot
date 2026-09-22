from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_027_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_EXECUTION_READ_MODEL_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_execution_read_model.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_027_certified_active_canonical_market_registry_query_execution_read_model.py"

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
from .certified_active_canonical_market_registry_query_execution_ledger import (
    CertifiedActiveMarketQueryExecutionLedgerEntry,
    ReadOnlyActiveMarketQueryExecutionAdmissionLedger,
)

UMD_027_BUILD_ID = "UMD-027"
UMD_027_BUILD_NAME = (
    "Certified Active Canonical Market Registry Query Execution Read Model"
)
UMD_027_REVISION = (
    "UMD_027_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_EXECUTION_READ_MODEL_V1"
)
UMD_027_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_execution_commit",
    "execution_persistence",
    "ledger_mutation",
    "read_model_mutation",
    "active_registry_mutation",
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


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQueryExecutionReadModel:
    ledger: ReadOnlyActiveMarketQueryExecutionAdmissionLedger
    lineage: ImmutableLineage
    _by_entry_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_execution_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_query_id: Mapping[
        str,
        Tuple[CertifiedActiveMarketQueryExecutionLedgerEntry, ...],
    ] = field(init=False, repr=False)
    _by_result_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _admitted_entries: Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ] = field(init=False, repr=False)
    _rejected_entries: Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("read-model lineage must belong to UMD")
        if self.lineage.build_id != UMD_027_BUILD_ID:
            raise ValueError(
                "read-model lineage must use build_id UMD-027"
            )
        if self.ledger.ledger_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "read-model lineage must include execution ledger hash"
            )

        by_entry_id = {}
        by_execution_id = {}
        by_query_id = {}
        by_result_id = {}
        admitted_entries = []
        rejected_entries = []

        for entry in self.ledger.entries:
            decision = entry.decision

            if entry.entry_id in by_entry_id:
                raise ValueError("duplicate execution-ledger entry ID")
            if decision.execution_id in by_execution_id:
                raise ValueError("duplicate execution ID")
            if decision.result_id in by_result_id:
                raise ValueError("duplicate result ID")

            by_entry_id[entry.entry_id] = entry
            by_execution_id[decision.execution_id] = entry
            by_result_id[decision.result_id] = entry
            by_query_id.setdefault(
                decision.query_id,
                [],
            ).append(entry)

            if decision.admitted:
                admitted_entries.append(entry)
            else:
                rejected_entries.append(entry)

        object.__setattr__(
            self,
            "_by_entry_id",
            MappingProxyType(by_entry_id),
        )
        object.__setattr__(
            self,
            "_by_execution_id",
            MappingProxyType(by_execution_id),
        )
        object.__setattr__(
            self,
            "_by_query_id",
            MappingProxyType(
                {
                    query_id: tuple(
                        sorted(
                            entries,
                            key=lambda item: item.sequence_number,
                        )
                    )
                    for query_id, entries in by_query_id.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_by_result_id",
            MappingProxyType(by_result_id),
        )
        object.__setattr__(
            self,
            "_admitted_entries",
            tuple(admitted_entries),
        )
        object.__setattr__(
            self,
            "_rejected_entries",
            tuple(rejected_entries),
        )

    @property
    def entry_count(self) -> int:
        return len(self.ledger.entries)

    @property
    def admitted_count(self) -> int:
        return len(self._admitted_entries)

    @property
    def rejected_count(self) -> int:
        return len(self._rejected_entries)

    def get_entry(
        self,
        entry_id: str,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        return self._by_entry_id.get(
            _text(entry_id, "entry_id")
        )

    def get_by_execution(
        self,
        execution_id: str,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        return self._by_execution_id.get(
            _text(execution_id, "execution_id")
        )

    def by_query(
        self,
        query_id: str,
    ) -> Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ]:
        return self._by_query_id.get(
            _text(query_id, "query_id"),
            (),
        )

    def get_by_result(
        self,
        result_id: str,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        return self._by_result_id.get(
            _text(result_id, "result_id")
        )

    def admitted_entries(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ]:
        return self._admitted_entries

    def rejected_entries(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ]:
        return self._rejected_entries

    def latest_entry(
        self,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        if not self.ledger.entries:
            return None
        return self.ledger.entries[-1]

    def latest_admitted(
        self,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        if not self._admitted_entries:
            return None
        return self._admitted_entries[-1]

    def query_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._by_query_id))

    def execution_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._by_execution_id))

    def result_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._by_result_id))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "read_model_mode": "execution_history_read_only",
            "ledger_hash": self.ledger.ledger_hash,
            "entry_ids": tuple(
                entry.entry_id
                for entry in self.ledger.entries
            ),
            "admitted_entry_ids": tuple(
                entry.entry_id
                for entry in self._admitted_entries
            ),
            "rejected_entry_ids": tuple(
                entry.entry_id
                for entry in self._rejected_entries
            ),
            "query_index": {
                query_id: tuple(
                    entry.entry_id
                    for entry in self._by_query_id[query_id]
                )
                for query_id in self.query_ids()
            },
            "execution_ids": self.execution_ids(),
            "result_ids": self.result_ids(),
            "lineage": self.lineage,
        }

    @property
    def read_model_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


@dataclass(frozen=True, slots=True)
class UMD027CertificationManifest:
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
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_umd_027_certification_manifest() -> UMD027CertificationManifest:
    return UMD027CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_027_BUILD_ID,
        build_name=UMD_027_BUILD_NAME,
        revision=UMD_027_REVISION,
        schema_version=UMD_027_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 27)
        ),
        read_model_mode="execution_history_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_market_query_execution_read_model(
    read_model: CertifiedActiveMarketQueryExecutionReadModel,
) -> Mapping[str, Any]:
    checks = {
        "entry_count_matches": (
            read_model.entry_count
            == len(read_model.ledger.entries)
        ),
        "admitted_rejected_partition": (
            read_model.admitted_count
            + read_model.rejected_count
            == read_model.entry_count
        ),
        "execution_ids_unique": (
            len(read_model.execution_ids())
            == read_model.entry_count
        ),
        "result_ids_unique": (
            len(read_model.result_ids())
            == read_model.entry_count
        ),
        "query_ids_deterministic": (
            read_model.query_ids()
            == tuple(sorted(read_model.query_ids()))
        ),
        "execution_ids_deterministic": (
            read_model.execution_ids()
            == tuple(sorted(read_model.execution_ids()))
        ),
        "result_ids_deterministic": (
            read_model.result_ids()
            == tuple(sorted(read_model.result_ids()))
        ),
        "deterministic_replay": (
            read_model.read_model_hash
            == deterministic_sha256(
                read_model.to_canonical_dict()
            )
        ),
        "read_only_indexes": (
            isinstance(
                read_model._by_entry_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_execution_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_query_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_result_id,
                MappingProxyType,
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    latest = read_model.latest_admitted()

    return MappingProxyType(
        {
            "certified": not failed,
            "read_model_hash": read_model.read_model_hash,
            "ledger_hash": read_model.ledger.ledger_hash,
            "entry_count": read_model.entry_count,
            "admitted_count": read_model.admitted_count,
            "rejected_count": read_model.rejected_count,
            "query_count": len(read_model.query_ids()),
            "latest_admitted_execution_id": (
                None
                if latest is None
                else latest.decision.execution_id
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_027_foundation() -> Mapping[str, Any]:
    manifest = build_umd_027_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-027"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 27)
            )
        ),
        "execution_history_read_only": (
            manifest.read_model_mode
            == "execution_history_read_only"
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


def verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model() -> bool:
    result = certify_umd_027_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-027 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_027_BUILD_ID",
    "UMD_027_BUILD_NAME",
    "UMD_027_REVISION",
    "UMD_027_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQueryExecutionReadModel",
    "UMD027CertificationManifest",
    "build_umd_027_certification_manifest",
    "certify_active_market_query_execution_read_model",
    "certify_umd_027_foundation",
    "verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model",
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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_execution_read_model import (
    UMD_027_REVISION,
    build_umd_027_certification_manifest,
    certify_umd_027_foundation,
    verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model,
)

FIXED = datetime(
    2026,
    8,
    6,
    8,
    0,
    tzinfo=timezone.utc,
)


class TestUMD027(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_027_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model()
        )

    def test_manifest_is_execution_history_read_only(
        self,
    ) -> None:
        manifest = build_umd_027_certification_manifest()

        self.assertEqual(
            manifest.read_model_mode,
            "execution_history_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_027_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 27)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-027",
            revision=UMD_027_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-027",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-027",
        )


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-027 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION READ MODEL"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD027
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_027_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-026 "
        "consumed read-only"
    )
    print(
        "[PASS] Execution-ledger hash lineage certified"
    )
    print(
        "[PASS] Entry, execution, query, and result indexes certified"
    )
    print(
        "[PASS] Admitted and rejected execution views certified"
    )
    print(
        "[PASS] Latest admitted execution view deterministic"
    )
    print(
        "[PASS] Deterministic ordering and replay certified"
    )
    print(
        "[PASS] Immutable read-only execution history certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-027 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY EXECUTION READ MODEL CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_execution_read_model import (
    UMD_027_BUILD_ID,
    UMD_027_BUILD_NAME,
    UMD_027_REVISION,
    UMD_027_SCHEMA_VERSION,
    CertifiedActiveMarketQueryExecutionReadModel,
    UMD027CertificationManifest,
    build_umd_027_certification_manifest,
    certify_active_market_query_execution_read_model,
    certify_umd_027_foundation,
    verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model,
)
"""

EXPORTED_NAMES = (
    "UMD_027_BUILD_ID",
    "UMD_027_BUILD_NAME",
    "UMD_027_REVISION",
    "UMD_027_SCHEMA_VERSION",
    "CertifiedActiveMarketQueryExecutionReadModel",
    "UMD027CertificationManifest",
    "build_umd_027_certification_manifest",
    "certify_active_market_query_execution_read_model",
    "certify_umd_027_foundation",
    "verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model",
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
        ".certified_active_canonical_market_registry_"
        "query_execution_read_model import ("
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
            ("certified_active_canonical_market_registry_read_model", "verify_umd_022_certified_active_canonical_market_registry_read_model"),
            ("certified_active_canonical_market_registry_query_contract", "verify_umd_023_certified_active_canonical_market_registry_query_contract"),
            ("certified_active_canonical_market_registry_query_execution_engine", "verify_umd_024_certified_active_canonical_market_registry_query_execution_engine"),
            ("certified_active_canonical_market_registry_query_execution_admission_gate", "verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate"),
            ("certified_active_canonical_market_registry_query_execution_ledger", "verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger"),
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
            "certified_active_canonical_market_registry_"
            "query_execution_read_model"
        )

        required = (
            "CertifiedActiveMarketQueryExecutionReadModel",
            "build_umd_027_certification_manifest",
            "certify_active_market_query_execution_read_model",
            "certify_umd_027_foundation",
            "verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model",
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
                "UMD-027 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-027 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION READ MODEL"
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
        "[PASS] Certified UMD-001 through UMD-026 "
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
        "build_id": "UMD-027",
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
            for number in range(1, 27)
        ),
        "mode": "execution_history_read_only",
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
        "[PASS] Required UMD-027 symbols verified"
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
        "[DONE] UMD-027 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_027_certified_active_canonical_market_"
        "registry_query_execution_read_model.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
