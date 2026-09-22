from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_terminal_production_read_only_certification import (
    OracleTerminalProductionReadOnlyCertificationReport,
    verify_oracle_terminal_production_read_only_certification_report,
)

SCHEMA_VERSION = "OIT-050"
ENGINE_ID = "OIT-050"
POLICY_ID = "oracle-terminal.final-freeze-and-completion.v1"

SUBSYSTEM_ID = "oracle_open_intelligence_terminal"
FINAL_MILESTONE = "OIT-050"
NEXT_SUBSYSTEM = "oracle_memory_and_continuous_intelligence_learner"


class OracleTerminalFinalFreezeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleTerminalFinalFreezeManifest:
    subsystem_id: str
    final_milestone: str
    source_production_certification_hash: str
    source_runner_certification_hash: str
    source_runner_sha256: str
    source_pipeline_certification_hash: str
    source_pipeline_report_hash: str
    source_pipeline_result_hash: str
    command_registry_certified: bool
    end_to_end_pipeline_certified: bool
    production_readiness_certified: bool
    read_only_boundary_frozen: bool
    publication_frozen_disabled: bool
    action_authorization_frozen_disabled: bool
    qseries_execution_frozen_disabled: bool
    persistent_memory_deferred: bool
    learning_deferred: bool
    no_further_oit_feature_layers_required: bool
    next_subsystem: str
    manifest_hash: str


@dataclass(frozen=True)
class OracleTerminalFinalFreezeCompletionReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    source_certification_report_hash: str
    freeze_manifest: OracleTerminalFinalFreezeManifest
    subsystem_completed: bool
    subsystem_frozen: bool
    terminal_production_ready: bool
    next_subsystem_authorized: bool
    further_oit_feature_builds_allowed: bool
    correction_builds_allowed_only_for_defects: bool
    persistent_memory_enabled: bool
    learning_update_performed: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    runtime_artifact_created: bool
    runtime_artifact_modified: bool
    networking_performed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    read_only: bool
    failure_reason: str | None
    report_hash: str


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
    raise OracleTerminalFinalFreezeInvariantError(
        "unsupported OIT-050 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_final_freeze_manifest(
    manifest: OracleTerminalFinalFreezeManifest,
) -> bool:
    body = asdict(manifest)
    supplied = body.pop("manifest_hash")

    if _stable_hash(body) != supplied:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 freeze manifest hash mismatch"
        )

    if manifest.subsystem_id != SUBSYSTEM_ID:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 subsystem identity mismatch"
        )

    if manifest.final_milestone != FINAL_MILESTONE:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 final milestone mismatch"
        )

    required_hashes = (
        manifest.source_production_certification_hash,
        manifest.source_runner_certification_hash,
        manifest.source_runner_sha256,
        manifest.source_pipeline_certification_hash,
        manifest.source_pipeline_report_hash,
        manifest.source_pipeline_result_hash,
    )
    if not all(required_hashes):
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 freeze lineage incomplete"
        )

    if len(manifest.source_runner_sha256) != 64:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 runner SHA-256 invalid"
        )

    required_true = (
        manifest.command_registry_certified,
        manifest.end_to_end_pipeline_certified,
        manifest.production_readiness_certified,
        manifest.read_only_boundary_frozen,
        manifest.publication_frozen_disabled,
        manifest.action_authorization_frozen_disabled,
        manifest.qseries_execution_frozen_disabled,
        manifest.persistent_memory_deferred,
        manifest.learning_deferred,
        manifest.no_further_oit_feature_layers_required,
    )
    if not all(required_true):
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 freeze guarantee missing"
        )

    if manifest.next_subsystem != NEXT_SUBSYSTEM:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 next subsystem mismatch"
        )

    return True


def build_oracle_terminal_final_freeze_completion_report(
    repository_root: str | Path,
    *,
    production_certification_report: (
        OracleTerminalProductionReadOnlyCertificationReport
    ),
) -> OracleTerminalFinalFreezeCompletionReport:
    root = Path(repository_root).resolve()

    verify_oracle_terminal_production_read_only_certification_report(
        production_certification_report
    )

    if not production_certification_report.production_readiness_certified:
        raise OracleTerminalFinalFreezeInvariantError(
            production_certification_report.failure_reason
            or "OIT-049 production readiness is not certified"
        )

    if not production_certification_report.final_freeze_ready:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-049 final-freeze readiness is not certified"
        )

    runner = production_certification_report.runner_certification
    pipeline = production_certification_report.pipeline_certification

    manifest_body = {
        "subsystem_id": SUBSYSTEM_ID,
        "final_milestone": FINAL_MILESTONE,
        "source_production_certification_hash": (
            production_certification_report.report_hash
        ),
        "source_runner_certification_hash": (
            runner.certification_hash
        ),
        "source_runner_sha256": runner.runner_sha256,
        "source_pipeline_certification_hash": (
            pipeline.certification_hash
        ),
        "source_pipeline_report_hash": (
            pipeline.pipeline_report_hash
        ),
        "source_pipeline_result_hash": (
            pipeline.pipeline_result_hash
        ),
        "command_registry_certified": (
            runner.command_registry.command_registry_certified
        ),
        "end_to_end_pipeline_certified": (
            pipeline.pipeline_certified
        ),
        "production_readiness_certified": (
            production_certification_report
            .production_readiness_certified
        ),
        "read_only_boundary_frozen": True,
        "publication_frozen_disabled": True,
        "action_authorization_frozen_disabled": True,
        "qseries_execution_frozen_disabled": True,
        "persistent_memory_deferred": True,
        "learning_deferred": True,
        "no_further_oit_feature_layers_required": True,
        "next_subsystem": NEXT_SUBSYSTEM,
    }
    manifest = OracleTerminalFinalFreezeManifest(
        **manifest_body,
        manifest_hash=_stable_hash(manifest_body),
    )
    verify_final_freeze_manifest(manifest)

    completed = bool(
        manifest.command_registry_certified
        and manifest.end_to_end_pipeline_certified
        and manifest.production_readiness_certified
        and manifest.read_only_boundary_frozen
        and manifest.no_further_oit_feature_layers_required
    )

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "completed_and_frozen",
        "repository_root": str(root),
        "source_certification_report_hash": (
            production_certification_report.report_hash
        ),
        "freeze_manifest": manifest,
        "subsystem_completed": completed,
        "subsystem_frozen": completed,
        "terminal_production_ready": completed,
        "next_subsystem_authorized": completed,
        "further_oit_feature_builds_allowed": False,
        "correction_builds_allowed_only_for_defects": True,
        "persistent_memory_enabled": False,
        "learning_update_performed": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": (
            None if completed else "OIT-050 freeze failed"
        ),
    }
    report = OracleTerminalFinalFreezeCompletionReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_oracle_terminal_final_freeze_completion_report(report)
    return report


def verify_oracle_terminal_final_freeze_completion_report(
    report: OracleTerminalFinalFreezeCompletionReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")

    if _stable_hash(body) != supplied:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 report hash mismatch"
        )

    if report.schema_version != SCHEMA_VERSION:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 schema mismatch"
        )

    if report.policy_id != POLICY_ID:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 policy mismatch"
        )

    if report.status != "completed_and_frozen":
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 completion status mismatch"
        )

    verify_final_freeze_manifest(report.freeze_manifest)

    if report.source_certification_report_hash != (
        report.freeze_manifest
        .source_production_certification_hash
    ):
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 certification lineage mismatch"
        )

    if not report.read_only:
        raise OracleTerminalFinalFreezeInvariantError(
            "OIT-050 report is not read-only"
        )

    if (
        report.further_oit_feature_builds_allowed
        or not report.correction_builds_allowed_only_for_defects
        or report.persistent_memory_enabled
        or report.learning_update_performed
        or report.analytics_execution_performed
        or report.database_access_performed
        or report.runtime_artifact_created
        or report.runtime_artifact_modified
        or report.networking_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleTerminalFinalFreezeInvariantError(
            "forbidden post-freeze capability enabled"
        )

    expected = bool(
        report.freeze_manifest.command_registry_certified
        and report.freeze_manifest.end_to_end_pipeline_certified
        and report.freeze_manifest.production_readiness_certified
        and report.freeze_manifest.read_only_boundary_frozen
        and report.freeze_manifest.no_further_oit_feature_layers_required
    )

    for value, label in (
        (report.subsystem_completed, "completion"),
        (report.subsystem_frozen, "freeze"),
        (report.terminal_production_ready, "production readiness"),
        (report.next_subsystem_authorized, "next subsystem authorization"),
    ):
        if value != expected:
            raise OracleTerminalFinalFreezeInvariantError(
                f"OIT-050 {label} state mismatch"
            )

    return True
