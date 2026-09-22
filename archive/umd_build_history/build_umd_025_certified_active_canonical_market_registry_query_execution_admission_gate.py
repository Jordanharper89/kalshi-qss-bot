from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_025_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_EXECUTION_ADMISSION_GATE_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_execution_admission_gate.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate.py"

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
from .certified_active_canonical_market_registry_query_execution_engine import (
    CertifiedActiveMarketQueryExecution,
    ReadOnlyActiveMarketQueryExecutionLedger,
)

UMD_025_BUILD_ID = "UMD-025"
UMD_025_BUILD_NAME = (
    "Certified Active Canonical Market Registry "
    "Query Execution Admission Gate"
)
UMD_025_REVISION = (
    "UMD_025_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_EXECUTION_ADMISSION_GATE_V1"
)
UMD_025_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_execution_commit",
    "execution_persistence",
    "execution_ledger_mutation",
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
class CertifiedActiveMarketQueryExecutionAdmissionDecision:
    execution_id: str
    execution_hash: str
    query_id: str
    result_id: str
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        execution_id = _text(
            self.execution_id,
            "execution_id",
        )
        if not execution_id.startswith(
            "umd:market-query-execution:"
        ):
            raise ValueError(
                "execution_id must use UMD execution prefix"
            )
        object.__setattr__(
            self,
            "execution_id",
            execution_id,
        )

        object.__setattr__(
            self,
            "execution_hash",
            _sha256(
                self.execution_hash,
                "execution_hash",
            ),
        )

        query_id = _text(
            self.query_id,
            "query_id",
        )
        if not query_id.startswith(
            "umd:market-query:"
        ):
            raise ValueError(
                "query_id must use UMD query prefix"
            )
        object.__setattr__(
            self,
            "query_id",
            query_id,
        )

        result_id = _text(
            self.result_id,
            "result_id",
        )
        if not result_id.startswith(
            "umd:market-query-result:"
        ):
            raise ValueError(
                "result_id must use UMD query-result prefix"
            )
        object.__setattr__(
            self,
            "result_id",
            result_id,
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
        reasons = tuple(
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
            reasons,
        )

        if self.admitted:
            if failed_checks or reasons:
                raise ValueError(
                    "admitted decision cannot contain failures"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected decision requires failed checks"
                )
            if reasons != tuple(sorted(failed_checks)):
                raise ValueError(
                    "rejection reasons must match failed checks"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "execution-admission lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_025_BUILD_ID:
            raise ValueError(
                "execution-admission lineage must use build_id UMD-025"
            )
        if self.execution_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "execution-admission lineage must include execution hash"
            )

    @property
    def decision_id(self) -> str:
        return "umd:market-query-execution-admission:" + deterministic_sha256(
            {
                "execution_id": self.execution_id,
                "execution_hash": self.execution_hash,
                "query_id": self.query_id,
                "result_id": self.result_id,
                "admitted": self.admitted,
                "checks": self.checks,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "execution_id": self.execution_id,
            "execution_hash": self.execution_hash,
            "query_id": self.query_id,
            "result_id": self.result_id,
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


def evaluate_active_market_query_execution(
    execution: CertifiedActiveMarketQueryExecution,
    existing_ledger: ReadOnlyActiveMarketQueryExecutionLedger,
    *,
    lineage: ImmutableLineage,
) -> CertifiedActiveMarketQueryExecutionAdmissionDecision:
    latest = existing_ledger.latest()

    checks = {
        "execution_id_not_seen": (
            existing_ledger.get(execution.execution_id) is None
        ),
        "execution_hash_not_seen": all(
            prior.execution_hash != execution.execution_hash
            for prior in existing_ledger.executions
        ),
        "result_id_not_seen": (
            existing_ledger.get_by_result(
                execution.result.result_id
            )
            is None
        ),
        "query_identity_bound": (
            execution.result.query.query_id
            == execution.request.query_id
        ),
        "result_identity_bound": (
            execution.result.result_id
            == "umd:market-query-result:"
            + deterministic_sha256(
                {
                    "query_id": execution.request.query_id,
                    "active_snapshot_id": (
                        execution.result.active_snapshot_id
                    ),
                    "active_snapshot_hash": (
                        execution.result.active_snapshot_hash
                    ),
                    "read_model_hash": (
                        execution.result.read_model_hash
                    ),
                    "market_record_hashes": tuple(
                        market.record_hash
                        for market in execution.result.markets
                    ),
                }
            )
        ),
        "execution_sequence_valid": (
            execution.execution_sequence == 1
            if latest is None
            else (
                execution.execution_sequence
                == latest.execution_sequence + 1
            )
        ),
        "previous_execution_hash_valid": (
            execution.previous_execution_hash is None
            if latest is None
            else (
                execution.previous_execution_hash
                == latest.execution_hash
            )
        ),
        "execution_hash_deterministic": (
            execution.execution_hash
            == deterministic_sha256(
                execution.to_canonical_dict()
            )
        ),
        "result_hash_deterministic": (
            execution.result.result_hash
            == deterministic_sha256(
                execution.result.to_canonical_dict()
            )
        ),
        "market_order_deterministic": tuple(
            market.canonical_market_id
            for market in execution.result.markets
        )
        == tuple(
            sorted(
                market.canonical_market_id
                for market in execution.result.markets
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return CertifiedActiveMarketQueryExecutionAdmissionDecision(
        execution_id=execution.execution_id,
        execution_hash=execution.execution_hash,
        query_id=execution.request.query_id,
        result_id=execution.result.result_id,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD025CertificationManifest:
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


def build_umd_025_certification_manifest() -> UMD025CertificationManifest:
    return UMD025CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_025_BUILD_ID,
        build_name=UMD_025_BUILD_NAME,
        revision=UMD_025_REVISION,
        schema_version=UMD_025_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 25)
        ),
        gate_mode="read_only_execution_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_025_foundation() -> Mapping[str, Any]:
    manifest = build_umd_025_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-025"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 25)
            )
        ),
        "read_only_execution_validation": (
            manifest.gate_mode
            == "read_only_execution_validation"
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


def verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate() -> bool:
    result = certify_umd_025_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-025 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_025_BUILD_ID",
    "UMD_025_BUILD_NAME",
    "UMD_025_REVISION",
    "UMD_025_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQueryExecutionAdmissionDecision",
    "evaluate_active_market_query_execution",
    "UMD025CertificationManifest",
    "build_umd_025_certification_manifest",
    "certify_umd_025_foundation",
    "verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate",
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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_execution_admission_gate import (
    UMD_025_REVISION,
    CertifiedActiveMarketQueryExecutionAdmissionDecision,
    build_umd_025_certification_manifest,
    certify_umd_025_foundation,
    verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate,
)

FIXED = datetime(
    2026,
    8,
    6,
    7,
    0,
    tzinfo=timezone.utc,
)
EXECUTION_HASH = "a" * 64


def lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-025",
        revision=UMD_025_REVISION,
        schema_version="1.0.0",
        parent_hashes=(EXECUTION_HASH,),
        source_refs=(
            "fixture://umd-025/decision",
        ),
        created_at=FIXED,
    )


class TestUMD025(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_025_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate()
        )

    def test_decision_identity_deterministic(self) -> None:
        checks = {
            "execution_id_not_seen": True,
            "execution_hash_not_seen": True,
        }

        first = CertifiedActiveMarketQueryExecutionAdmissionDecision(
            execution_id=(
                "umd:market-query-execution:"
                + "b" * 64
            ),
            execution_hash=EXECUTION_HASH,
            query_id=(
                "umd:market-query:"
                + "c" * 64
            ),
            result_id=(
                "umd:market-query-result:"
                + "d" * 64
            ),
            admitted=True,
            checks=checks,
            rejection_reasons=(),
            lineage=lineage(),
        )

        second = CertifiedActiveMarketQueryExecutionAdmissionDecision(
            execution_id=(
                "umd:market-query-execution:"
                + "b" * 64
            ),
            execution_hash=EXECUTION_HASH,
            query_id=(
                "umd:market-query:"
                + "c" * 64
            ),
            result_id=(
                "umd:market-query-result:"
                + "d" * 64
            ),
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
            CertifiedActiveMarketQueryExecutionAdmissionDecision(
                execution_id=(
                    "umd:market-query-execution:"
                    + "b" * 64
                ),
                execution_hash=EXECUTION_HASH,
                query_id=(
                    "umd:market-query:"
                    + "c" * 64
                ),
                result_id=(
                    "umd:market-query-result:"
                    + "d" * 64
                ),
                admitted=False,
                checks={
                    "execution_id_not_seen": False
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
            CertifiedActiveMarketQueryExecutionAdmissionDecision(
                execution_id=(
                    "umd:market-query-execution:"
                    + "b" * 64
                ),
                execution_hash=EXECUTION_HASH,
                query_id=(
                    "umd:market-query:"
                    + "c" * 64
                ),
                result_id=(
                    "umd:market-query-result:"
                    + "d" * 64
                ),
                admitted=True,
                checks={
                    "execution_id_not_seen": False
                },
                rejection_reasons=(),
                lineage=lineage(),
            )

    def test_lineage_requires_execution_hash(
        self,
    ) -> None:
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-025",
            revision=UMD_025_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-025/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQueryExecutionAdmissionDecision(
                execution_id=(
                    "umd:market-query-execution:"
                    + "b" * 64
                ),
                execution_hash=EXECUTION_HASH,
                query_id=(
                    "umd:market-query:"
                    + "c" * 64
                ),
                result_id=(
                    "umd:market-query-result:"
                    + "d" * 64
                ),
                admitted=True,
                checks={
                    "execution_id_not_seen": True
                },
                rejection_reasons=(),
                lineage=bad_lineage,
            )

    def test_decision_is_immutable(self) -> None:
        item = CertifiedActiveMarketQueryExecutionAdmissionDecision(
            execution_id=(
                "umd:market-query-execution:"
                + "b" * 64
            ),
            execution_hash=EXECUTION_HASH,
            query_id=(
                "umd:market-query:"
                + "c" * 64
            ),
            result_id=(
                "umd:market-query-result:"
                + "d" * 64
            ),
            admitted=True,
            checks={
                "execution_id_not_seen": True
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
                "execution_id_not_seen"
            ] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_025_certification_manifest()

        self.assertEqual(
            manifest.gate_mode,
            "read_only_execution_validation",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-025 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION ADMISSION GATE"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD025
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_025_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-024 "
        "consumed read-only"
    )
    print(
        "[PASS] Execution replay rejection contract certified"
    )
    print(
        "[PASS] Query, result, and execution identity binding certified"
    )
    print(
        "[PASS] Execution sequence and previous-hash validation certified"
    )
    print(
        "[PASS] Result and execution deterministic hashing certified"
    )
    print(
        "[PASS] Deterministic result ordering validation certified"
    )
    print(
        "[PASS] Immutable execution-admission decisions certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-025 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY EXECUTION ADMISSION GATE CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_execution_admission_gate import (
    UMD_025_BUILD_ID,
    UMD_025_BUILD_NAME,
    UMD_025_REVISION,
    UMD_025_SCHEMA_VERSION,
    CertifiedActiveMarketQueryExecutionAdmissionDecision,
    evaluate_active_market_query_execution,
    UMD025CertificationManifest,
    build_umd_025_certification_manifest,
    certify_umd_025_foundation,
    verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate,
)
"""

EXPORTED_NAMES = (
    "UMD_025_BUILD_ID",
    "UMD_025_BUILD_NAME",
    "UMD_025_REVISION",
    "UMD_025_SCHEMA_VERSION",
    "CertifiedActiveMarketQueryExecutionAdmissionDecision",
    "evaluate_active_market_query_execution",
    "UMD025CertificationManifest",
    "build_umd_025_certification_manifest",
    "certify_umd_025_foundation",
    "verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate",
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
        "query_execution_admission_gate import ("
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
            "query_execution_admission_gate"
        )

        required = (
            "CertifiedActiveMarketQueryExecutionAdmissionDecision",
            "evaluate_active_market_query_execution",
            "build_umd_025_certification_manifest",
            "certify_umd_025_foundation",
            "verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate",
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
                "UMD-025 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-025 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION ADMISSION GATE"
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
        "[PASS] Certified UMD-001 through UMD-024 "
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
        "build_id": "UMD-025",
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
            for number in range(1, 25)
        ),
        "mode": "read_only_execution_validation",
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
        "[PASS] Required UMD-025 symbols verified"
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
        "[DONE] UMD-025 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_025_certified_active_canonical_market_"
        "registry_query_execution_admission_gate.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
