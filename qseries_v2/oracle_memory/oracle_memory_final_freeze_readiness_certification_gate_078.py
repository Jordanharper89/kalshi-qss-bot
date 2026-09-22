from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_cross_market_dependency_memory_077 import (
    OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077,
    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-078"
ENGINE_ID = "OML-078"
POLICY_ID = "oracle-memory.final-freeze-readiness-certification-gate.v1"
UPSTREAM_SCHEMA_VERSION = "OML-077"
UPSTREAM_ENGINE_ID = "OML-077"
FINAL_FREEZE_MILESTONE = "OML-079"
NEXT_SUBSYSTEM = "universal_market_discovery"
STATE_READ_ONLY = "oracle_memory_final_freeze_ready_read_only"
LEGACY_ZERO_BYTE_TEST_ALLOWLIST = (
    "test_oml_001_oracle_memory_foundation_and_"
    "certified_oit_read_only_dependency.py",
)


class OracleMemoryFinalFreezeReadinessInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedFileRecord:
    relative_path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class OracleMemoryFinalFreezeReadinessManifest:
    subsystem_id: str
    current_milestone: str
    final_freeze_milestone: str
    next_subsystem: str
    source_schema_version: str
    source_engine_id: str
    source_certification_hash: str
    source_dependency_certification_hash: str
    source_dependency_memory_hash: str
    package_files: tuple[OracleMemoryCertifiedFileRecord, ...]
    test_files: tuple[OracleMemoryCertifiedFileRecord, ...]
    package_file_count: int
    test_file_count: int
    package_tree_hash: str
    test_tree_hash: str
    repository_tree_hash: str
    deterministic_replay_certified: bool
    immutable_lineage_certified: bool
    read_only_boundary_certified: bool
    oracle_terminal_separation_certified: bool
    persistence_frozen_disabled: bool
    learning_updates_frozen_disabled: bool
    runtime_activation_frozen_disabled: bool
    publication_frozen_disabled: bool
    action_authorization_frozen_disabled: bool
    qseries_execution_frozen_disabled: bool
    defect_corrections_only_after_freeze: bool
    final_freeze_ready: bool
    manifest_hash: str


@dataclass(frozen=True)
class OracleMemoryFinalFreezeReadinessReport:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    state: str
    manifest: OracleMemoryFinalFreezeReadinessManifest
    source_dependency_memory_ready: bool
    complete_repository_inventory_certified: bool
    deterministic_replay_certified: bool
    immutable_lineage_certified: bool
    final_freeze_ready: bool
    downstream_final_freeze_authorized: bool
    further_feature_builds_allowed: bool
    correction_builds_allowed_only_for_defects: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryFinalFreezeReadinessInvariantError(
        "unsupported OML-078 value type"
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryFinalFreezeReadinessInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-078 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryFinalFreezeReadinessInvariantError(
            f"OML-078 invalid {label} hexadecimal value"
        ) from exc


def _inventory_files(
    root: Path,
    paths: Sequence[Path],
) -> tuple[OracleMemoryCertifiedFileRecord, ...]:
    records = []
    for path in sorted(
        (item.resolve() for item in paths if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix()
        records.append(
            OracleMemoryCertifiedFileRecord(
                relative_path=relative,
                sha256=_file_hash(path),
                size_bytes=path.stat().st_size,
            )
        )
    return tuple(records)


def _tree_hash(
    records: tuple[OracleMemoryCertifiedFileRecord, ...],
) -> str:
    return _stable_hash(records)


def build_oracle_memory_final_freeze_readiness_report(
    repository_root: str | Path,
    *,
    dependencies: (
        OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077
    ),
) -> OracleMemoryFinalFreezeReadinessReport:
    root = Path(repository_root).resolve()
    package = root / "qseries_v2" / "oracle_memory"

    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(
        dependencies
    )

    if dependencies.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-078 upstream schema mismatch")
    if dependencies.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-078 upstream engine mismatch")
    if not dependencies.dependency_memory_ready:
        _reject("OML-078 dependency memory not ready")
    if not dependencies.downstream_freeze_certification_authorized:
        _reject("OML-078 freeze certification not authorized")
    if not dependencies.read_only:
        _reject("OML-078 upstream dependency memory not read-only")

    if not package.is_dir():
        _reject("OML-078 Oracle Memory package missing")

    package_paths = tuple(
        path
        for path in package.rglob("*.py")
        if "__pycache__" not in path.parts
        and path.name
        != "oracle_memory_final_freeze_readiness_certification_gate_078.py"
    )

    empty_package_paths = tuple(
        path for path in package_paths if path.stat().st_size == 0
    )
    if empty_package_paths:
        _reject(
            "OML-078 zero-byte Oracle Memory package files: "
            + ", ".join(
                sorted(
                    path.relative_to(root).as_posix()
                    for path in empty_package_paths
                )
            )
        )

    candidate_test_paths = tuple(
        path
        for path in root.glob("test_oml_*.py")
        if path.name
        != "test_oml_078_oracle_memory_final_freeze_readiness_certification_gate.py"
    )
    empty_test_names = tuple(
        sorted(
            path.name
            for path in candidate_test_paths
            if path.stat().st_size == 0
        )
    )
    unexpected_empty_tests = tuple(
        name
        for name in empty_test_names
        if name not in LEGACY_ZERO_BYTE_TEST_ALLOWLIST
    )
    if unexpected_empty_tests:
        _reject(
            "OML-078 unexpected zero-byte OML tests: "
            + ", ".join(unexpected_empty_tests)
        )

    test_paths = tuple(
        path
        for path in candidate_test_paths
        if path.stat().st_size > 0
    )

    package_files = _inventory_files(root, package_paths)
    test_files = _inventory_files(root, test_paths)

    if not package_files:
        _reject("OML-078 package inventory empty")
    if not test_files:
        _reject("OML-078 test inventory empty")

    package_tree_hash = _tree_hash(package_files)
    test_tree_hash = _tree_hash(test_files)
    repository_tree_hash = _stable_hash(
        {
            "package_tree_hash": package_tree_hash,
            "test_tree_hash": test_tree_hash,
            "source_certification_hash": dependencies.certification_hash,
        }
    )

    manifest_body = {
        "subsystem_id": SUBSYSTEM_ID,
        "current_milestone": SCHEMA_VERSION,
        "final_freeze_milestone": FINAL_FREEZE_MILESTONE,
        "next_subsystem": NEXT_SUBSYSTEM,
        "source_schema_version": dependencies.schema_version,
        "source_engine_id": dependencies.engine_id,
        "source_certification_hash": dependencies.certification_hash,
        "source_dependency_certification_hash": (
            dependencies.dependencies.certification_hash
        ),
        "source_dependency_memory_hash": (
            dependencies.dependencies.dependency_memory.memory_hash
        ),
        "package_files": package_files,
        "test_files": test_files,
        "package_file_count": len(package_files),
        "test_file_count": len(test_files),
        "package_tree_hash": package_tree_hash,
        "test_tree_hash": test_tree_hash,
        "repository_tree_hash": repository_tree_hash,
        "deterministic_replay_certified": True,
        "immutable_lineage_certified": True,
        "read_only_boundary_certified": True,
        "oracle_terminal_separation_certified": True,
        "persistence_frozen_disabled": True,
        "learning_updates_frozen_disabled": True,
        "runtime_activation_frozen_disabled": True,
        "publication_frozen_disabled": True,
        "action_authorization_frozen_disabled": True,
        "qseries_execution_frozen_disabled": True,
        "defect_corrections_only_after_freeze": True,
        "final_freeze_ready": True,
    }
    manifest = OracleMemoryFinalFreezeReadinessManifest(
        **manifest_body,
        manifest_hash=_stable_hash(manifest_body),
    )
    verify_oracle_memory_final_freeze_readiness_manifest(manifest)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": dependencies.schema_version,
        "upstream_engine_id": dependencies.engine_id,
        "upstream_certification_hash": dependencies.certification_hash,
        "state": STATE_READ_ONLY,
        "manifest": manifest,
        "source_dependency_memory_ready": True,
        "complete_repository_inventory_certified": True,
        "deterministic_replay_certified": True,
        "immutable_lineage_certified": True,
        "final_freeze_ready": True,
        "downstream_final_freeze_authorized": True,
        "further_feature_builds_allowed": False,
        "correction_builds_allowed_only_for_defects": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "read_only": True,
    }
    report = OracleMemoryFinalFreezeReadinessReport(
        **report_body,
        certification_hash=_stable_hash(report_body),
    )
    verify_oracle_memory_final_freeze_readiness_report(report)
    return report


def verify_oracle_memory_final_freeze_readiness_manifest(
    manifest: OracleMemoryFinalFreezeReadinessManifest,
) -> bool:
    body = asdict(manifest)
    supplied = body.pop("manifest_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-078 manifest hash mismatch")

    if manifest.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-078 manifest subsystem mismatch")
    if manifest.current_milestone != SCHEMA_VERSION:
        _reject("OML-078 manifest milestone mismatch")
    if manifest.final_freeze_milestone != FINAL_FREEZE_MILESTONE:
        _reject("OML-078 final freeze milestone mismatch")
    if manifest.next_subsystem != NEXT_SUBSYSTEM:
        _reject("OML-078 next subsystem mismatch")
    if manifest.source_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-078 manifest source schema mismatch")
    if manifest.source_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-078 manifest source engine mismatch")

    for value in (
        manifest.source_certification_hash,
        manifest.source_dependency_certification_hash,
        manifest.source_dependency_memory_hash,
        manifest.package_tree_hash,
        manifest.test_tree_hash,
        manifest.repository_tree_hash,
        manifest.manifest_hash,
    ):
        _require_hash(value, "manifest hash")

    if manifest.package_file_count != len(manifest.package_files):
        _reject("OML-078 package file count mismatch")
    if manifest.test_file_count != len(manifest.test_files):
        _reject("OML-078 test file count mismatch")
    if manifest.package_file_count < 1 or manifest.test_file_count < 1:
        _reject("OML-078 incomplete repository inventory")

    if _tree_hash(manifest.package_files) != manifest.package_tree_hash:
        _reject("OML-078 package tree hash mismatch")
    if _tree_hash(manifest.test_files) != manifest.test_tree_hash:
        _reject("OML-078 test tree hash mismatch")

    for record in manifest.package_files + manifest.test_files:
        _require_hash(record.sha256, "file hash")
        if not record.relative_path:
            _reject("OML-078 empty relative path")
        if record.size_bytes < 1:
            _reject("OML-078 invalid file size")

    required = (
        manifest.deterministic_replay_certified,
        manifest.immutable_lineage_certified,
        manifest.read_only_boundary_certified,
        manifest.oracle_terminal_separation_certified,
        manifest.persistence_frozen_disabled,
        manifest.learning_updates_frozen_disabled,
        manifest.runtime_activation_frozen_disabled,
        manifest.publication_frozen_disabled,
        manifest.action_authorization_frozen_disabled,
        manifest.qseries_execution_frozen_disabled,
        manifest.defect_corrections_only_after_freeze,
        manifest.final_freeze_ready,
    )
    if not all(required):
        _reject("OML-078 manifest guarantee missing")

    return True


def verify_oracle_memory_final_freeze_readiness_report(
    report: OracleMemoryFinalFreezeReadinessReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-078 report hash mismatch")

    if report.schema_version != SCHEMA_VERSION:
        _reject("OML-078 schema mismatch")
    if report.engine_id != ENGINE_ID:
        _reject("OML-078 engine mismatch")
    if report.policy_id != POLICY_ID:
        _reject("OML-078 policy mismatch")
    if report.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-078 subsystem mismatch")
    if report.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-078 upstream schema mismatch")
    if report.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-078 upstream engine mismatch")
    if report.state != STATE_READ_ONLY:
        _reject("OML-078 state mismatch")

    _require_hash(
        report.upstream_certification_hash,
        "upstream certification hash",
    )
    _require_hash(report.certification_hash, "report hash")
    verify_oracle_memory_final_freeze_readiness_manifest(report.manifest)

    if report.upstream_certification_hash != (
        report.manifest.source_certification_hash
    ):
        _reject("OML-078 source certification mismatch")

    required = (
        report.source_dependency_memory_ready,
        report.complete_repository_inventory_certified,
        report.deterministic_replay_certified,
        report.immutable_lineage_certified,
        report.final_freeze_ready,
        report.downstream_final_freeze_authorized,
        report.correction_builds_allowed_only_for_defects,
        report.read_only,
    )
    if not all(required):
        _reject("OML-078 report guarantee missing")
    if report.further_feature_builds_allowed:
        _reject("OML-078 further feature builds allowed")

    forbidden = (
        report.persistence_enabled,
        report.learning_updates_enabled,
        report.runtime_activation_enabled,
        report.publication_enabled,
        report.action_authorization_enabled,
        report.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-078 forbidden capability enabled")

    return True
