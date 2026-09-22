from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_024_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_EXECUTION_ENGINE_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_execution_engine.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_024_certified_active_canonical_market_registry_query_execution_engine.py"

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
from .certified_active_canonical_market_registry_read_model import (
    CertifiedActiveCanonicalMarketRegistryReadModel,
)
from .certified_active_canonical_market_registry_query_contract import (
    CertifiedActiveMarketQueryRequest,
    CertifiedActiveMarketQueryResult,
    execute_active_market_query,
)

UMD_024_BUILD_ID = "UMD-024"
UMD_024_BUILD_NAME = (
    "Certified Active Canonical Market Registry Query Execution Engine"
)
UMD_024_REVISION = (
    "UMD_024_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_EXECUTION_ENGINE_V1"
)
UMD_024_SCHEMA_VERSION = "1.0.0"

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
class CertifiedActiveMarketQueryExecution:
    execution_sequence: int
    previous_execution_hash: str | None
    request: CertifiedActiveMarketQueryRequest
    result: CertifiedActiveMarketQueryResult
    executed_at: datetime
    execution_context: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        if not isinstance(self.execution_sequence, int):
            raise TypeError("execution_sequence must be an integer")
        if self.execution_sequence < 1:
            raise ValueError("execution_sequence must be positive")

        if self.previous_execution_hash is None:
            if self.execution_sequence != 1:
                raise ValueError(
                    "only the first execution may omit previous_execution_hash"
                )
        else:
            object.__setattr__(
                self,
                "previous_execution_hash",
                _sha256(
                    self.previous_execution_hash,
                    "previous_execution_hash",
                ),
            )

        if self.result.query.query_id != self.request.query_id:
            raise ValueError(
                "result query does not match execution request"
            )

        object.__setattr__(
            self,
            "executed_at",
            _utc(self.executed_at, "executed_at"),
        )
        object.__setattr__(
            self,
            "execution_context",
            _freeze(self.execution_context),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("execution lineage must belong to UMD")
        if self.lineage.build_id != UMD_024_BUILD_ID:
            raise ValueError(
                "execution lineage must use build_id UMD-024"
            )

        required_parents = {
            self.result.result_hash,
            self.result.read_model_hash,
        }
        if self.previous_execution_hash is not None:
            required_parents.add(self.previous_execution_hash)

        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "execution lineage is missing required parent hashes"
            )

    @property
    def execution_id(self) -> str:
        return "umd:market-query-execution:" + deterministic_sha256(
            {
                "execution_sequence": self.execution_sequence,
                "previous_execution_hash": self.previous_execution_hash,
                "query_id": self.request.query_id,
                "result_id": self.result.result_id,
                "active_snapshot_id": self.result.active_snapshot_id,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "execution_id": self.execution_id,
            "execution_sequence": self.execution_sequence,
            "previous_execution_hash": self.previous_execution_hash,
            "request": self.request,
            "result": self.result,
            "executed_at": self.executed_at,
            "execution_context": self.execution_context,
            "lineage": self.lineage,
        }

    @property
    def execution_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )

    def summary(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "execution_id": self.execution_id,
                "query_id": self.request.query_id,
                "query_mode": self.request.query_mode.value,
                "active_snapshot_id": self.result.active_snapshot_id,
                "active_snapshot_hash": self.result.active_snapshot_hash,
                "market_count": len(self.result.markets),
                "market_ids": tuple(
                    market.canonical_market_id
                    for market in self.result.markets
                ),
                "result_hash": self.result.result_hash,
                "execution_hash": self.execution_hash,
            }
        )


@dataclass(frozen=True, slots=True)
class ReadOnlyActiveMarketQueryExecutionLedger:
    executions: Tuple[CertifiedActiveMarketQueryExecution, ...]
    ledger_lineage: ImmutableLineage
    _by_execution_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecution,
    ] = field(init=False, repr=False)
    _by_query_id: Mapping[
        str,
        Tuple[CertifiedActiveMarketQueryExecution, ...],
    ] = field(init=False, repr=False)
    _by_result_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecution,
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(
                self.executions,
                key=lambda execution: execution.execution_sequence,
            )
        )
        object.__setattr__(self, "executions", ordered)

        if self.ledger_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("execution-ledger lineage must belong to UMD")
        if self.ledger_lineage.build_id != UMD_024_BUILD_ID:
            raise ValueError(
                "execution-ledger lineage must use build_id UMD-024"
            )

        by_execution_id = {}
        by_query_id = {}
        by_result_id = {}
        previous_execution = None

        for expected_sequence, execution in enumerate(
            ordered,
            start=1,
        ):
            if execution.execution_sequence != expected_sequence:
                raise ValueError(
                    "execution sequence must be contiguous and start at 1"
                )

            if previous_execution is None:
                if execution.previous_execution_hash is not None:
                    raise ValueError(
                        "first execution must not have previous hash"
                    )
            else:
                if (
                    execution.previous_execution_hash
                    != previous_execution.execution_hash
                ):
                    raise ValueError(
                        "previous-execution hash chain mismatch"
                    )

            if execution.execution_id in by_execution_id:
                raise ValueError("duplicate execution ID")
            if execution.result.result_id in by_result_id:
                raise ValueError(
                    "query result may be executed only once"
                )

            by_execution_id[execution.execution_id] = execution
            by_result_id[execution.result.result_id] = execution
            by_query_id.setdefault(
                execution.request.query_id,
                [],
            ).append(execution)

            previous_execution = execution

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
                    query_id: tuple(values)
                    for query_id, values in by_query_id.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_by_result_id",
            MappingProxyType(by_result_id),
        )

    def get(
        self,
        execution_id: str,
    ) -> CertifiedActiveMarketQueryExecution | None:
        return self._by_execution_id.get(
            _text(execution_id, "execution_id")
        )

    def by_query(
        self,
        query_id: str,
    ) -> Tuple[CertifiedActiveMarketQueryExecution, ...]:
        return self._by_query_id.get(
            _text(query_id, "query_id"),
            (),
        )

    def get_by_result(
        self,
        result_id: str,
    ) -> CertifiedActiveMarketQueryExecution | None:
        return self._by_result_id.get(
            _text(result_id, "result_id")
        )

    def latest(
        self,
    ) -> CertifiedActiveMarketQueryExecution | None:
        if not self.executions:
            return None
        return self.executions[-1]

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "ledger_mode": "append_only_read_only",
            "executions": self.executions,
            "ledger_lineage": self.ledger_lineage,
        }

    @property
    def ledger_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def execute_certified_active_market_query(
    request: CertifiedActiveMarketQueryRequest,
    read_model: CertifiedActiveCanonicalMarketRegistryReadModel,
    *,
    execution_sequence: int,
    previous_execution_hash: str | None,
    executed_at: datetime,
    execution_context: Mapping[str, Any],
    result_lineage: ImmutableLineage,
    execution_lineage: ImmutableLineage,
) -> CertifiedActiveMarketQueryExecution:
    result = execute_active_market_query(
        request,
        read_model,
        lineage=result_lineage,
    )

    return CertifiedActiveMarketQueryExecution(
        execution_sequence=execution_sequence,
        previous_execution_hash=previous_execution_hash,
        request=request,
        result=result,
        executed_at=executed_at,
        execution_context=execution_context,
        lineage=execution_lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD024CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    engine_mode: str
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
            "engine_mode": self.engine_mode,
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


def build_umd_024_certification_manifest() -> UMD024CertificationManifest:
    return UMD024CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_024_BUILD_ID,
        build_name=UMD_024_BUILD_NAME,
        revision=UMD_024_REVISION,
        schema_version=UMD_024_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 24)
        ),
        engine_mode="deterministic_read_only_execution",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_market_query_execution_ledger(
    ledger: ReadOnlyActiveMarketQueryExecutionLedger,
) -> Mapping[str, Any]:
    checks = {
        "execution_ids_unique": len(
            {
                execution.execution_id
                for execution in ledger.executions
            }
        )
        == len(ledger.executions),
        "result_ids_unique": len(
            {
                execution.result.result_id
                for execution in ledger.executions
            }
        )
        == len(ledger.executions),
        "sequence_contiguous": tuple(
            execution.execution_sequence
            for execution in ledger.executions
        )
        == tuple(range(1, len(ledger.executions) + 1)),
        "deterministic_replay": (
            ledger.ledger_hash
            == deterministic_sha256(
                ledger.to_canonical_dict()
            )
        ),
        "read_only_indexes": (
            isinstance(
                ledger._by_execution_id,
                MappingProxyType,
            )
            and isinstance(
                ledger._by_query_id,
                MappingProxyType,
            )
            and isinstance(
                ledger._by_result_id,
                MappingProxyType,
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    latest = ledger.latest()

    return MappingProxyType(
        {
            "certified": not failed,
            "ledger_hash": ledger.ledger_hash,
            "execution_count": len(ledger.executions),
            "latest_execution_id": (
                None
                if latest is None
                else latest.execution_id
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_024_foundation() -> Mapping[str, Any]:
    manifest = build_umd_024_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-024"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 24)
            )
        ),
        "deterministic_read_only_execution": (
            manifest.engine_mode
            == "deterministic_read_only_execution"
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


def verify_umd_024_certified_active_canonical_market_registry_query_execution_engine() -> bool:
    result = certify_umd_024_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-024 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_024_BUILD_ID",
    "UMD_024_BUILD_NAME",
    "UMD_024_REVISION",
    "UMD_024_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQueryExecution",
    "ReadOnlyActiveMarketQueryExecutionLedger",
    "execute_certified_active_market_query",
    "UMD024CertificationManifest",
    "build_umd_024_certification_manifest",
    "certify_active_market_query_execution_ledger",
    "certify_umd_024_foundation",
    "verify_umd_024_certified_active_canonical_market_registry_query_execution_engine",
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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_execution_engine import (
    UMD_024_REVISION,
    build_umd_024_certification_manifest,
    certify_umd_024_foundation,
    verify_umd_024_certified_active_canonical_market_registry_query_execution_engine,
)

FIXED = datetime(
    2026,
    8,
    6,
    6,
    30,
    tzinfo=timezone.utc,
)


class TestUMD024(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_024_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_024_certified_active_canonical_market_registry_query_execution_engine()
        )

    def test_manifest_is_deterministic_read_only(
        self,
    ) -> None:
        manifest = build_umd_024_certification_manifest()

        self.assertEqual(
            manifest.engine_mode,
            "deterministic_read_only_execution",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_024_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 24)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-024",
            revision=UMD_024_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-024",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-024",
        )

    def test_lineage_is_immutable(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-024",
            revision=UMD_024_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-024",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            lineage.build_id = "MUTATED"


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-024 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION ENGINE"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD024
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_024_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-023 "
        "consumed read-only"
    )
    print(
        "[PASS] Certified query execution contract registered"
    )
    print(
        "[PASS] Query request and result identity binding certified"
    )
    print(
        "[PASS] Execution sequence and previous-hash chaining certified"
    )
    print(
        "[PASS] Duplicate result replay rejection certified"
    )
    print(
        "[PASS] Deterministic execution summaries certified"
    )
    print(
        "[PASS] Read-only execution ledger certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-024 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY EXECUTION ENGINE CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_execution_engine import (
    UMD_024_BUILD_ID,
    UMD_024_BUILD_NAME,
    UMD_024_REVISION,
    UMD_024_SCHEMA_VERSION,
    CertifiedActiveMarketQueryExecution,
    ReadOnlyActiveMarketQueryExecutionLedger,
    execute_certified_active_market_query,
    UMD024CertificationManifest,
    build_umd_024_certification_manifest,
    certify_active_market_query_execution_ledger,
    certify_umd_024_foundation,
    verify_umd_024_certified_active_canonical_market_registry_query_execution_engine,
)
"""

EXPORTED_NAMES = (
    "UMD_024_BUILD_ID",
    "UMD_024_BUILD_NAME",
    "UMD_024_REVISION",
    "UMD_024_SCHEMA_VERSION",
    "CertifiedActiveMarketQueryExecution",
    "ReadOnlyActiveMarketQueryExecutionLedger",
    "execute_certified_active_market_query",
    "UMD024CertificationManifest",
    "build_umd_024_certification_manifest",
    "certify_active_market_query_execution_ledger",
    "certify_umd_024_foundation",
    "verify_umd_024_certified_active_canonical_market_registry_query_execution_engine",
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
        ".certified_active_canonical_market_registry_query_execution_engine "
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
            ("certified_active_canonical_market_registry_read_model", "verify_umd_022_certified_active_canonical_market_registry_read_model"),
            ("certified_active_canonical_market_registry_query_contract", "verify_umd_023_certified_active_canonical_market_registry_query_contract"),
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
            "certified_active_canonical_market_registry_query_execution_engine"
        )

        required = (
            "CertifiedActiveMarketQueryExecution",
            "ReadOnlyActiveMarketQueryExecutionLedger",
            "execute_certified_active_market_query",
            "build_umd_024_certification_manifest",
            "certify_active_market_query_execution_ledger",
            "certify_umd_024_foundation",
            "verify_umd_024_certified_active_canonical_market_registry_query_execution_engine",
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
                "UMD-024 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_024_certified_active_canonical_market_registry_query_execution_engine()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-024 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION ENGINE"
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
        "[PASS] Certified UMD-001 through UMD-023 "
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
        "build_id": "UMD-024",
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
            for number in range(1, 24)
        ),
        "mode": "deterministic_read_only_execution",
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
        "[PASS] Required UMD-024 symbols verified"
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
        "[DONE] UMD-024 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_024_certified_active_canonical_market_"
        "registry_query_execution_engine.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
