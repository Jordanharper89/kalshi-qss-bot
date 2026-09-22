from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (
    NEXT_SUBSYSTEM,
    OracleTerminalFinalFreezeCompletionReport,
    verify_oracle_terminal_final_freeze_completion_report,
)

SCHEMA_VERSION = "OML-001"
ENGINE_ID = "OML-001"
POLICY_ID = (
    "oracle-memory-continuous-intelligence-learner.foundation.v1"
)

SUBSYSTEM_ID = "oracle_memory_and_continuous_intelligence_learner"
UPSTREAM_SUBSYSTEM_ID = "oracle_open_intelligence_terminal"
UPSTREAM_FINAL_MILESTONE = "OIT-050"

MEMORY_DOMAINS = (
    "entity_memory",
    "source_reliability_memory",
    "market_behavior_memory",
    "calibration_memory",
    "causal_memory",
    "narrative_memory",
    "knowledge_graph_memory",
    "meta_learning_memory",
)


class OracleMemoryLearnerFoundationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryLearnerUpstreamCertification:
    upstream_subsystem_id: str
    upstream_final_milestone: str
    upstream_report_hash: str
    upstream_runner_sha256: str
    upstream_completed: bool
    upstream_frozen: bool
    upstream_production_ready: bool
    upstream_read_only_boundary_frozen: bool
    upstream_publication_disabled: bool
    upstream_action_authorization_disabled: bool
    upstream_qseries_execution_disabled: bool
    downstream_subsystem_authorized: bool
    certification_hash: str


@dataclass(frozen=True)
class OracleMemoryLearnerFoundationReport:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    repository_root: str
    upstream_certification: OracleMemoryLearnerUpstreamCertification
    package_separate_from_oracle_terminal: bool
    certified_read_only_upstream_consumption_only: bool
    deterministic_contract_enabled: bool
    replay_verification_enabled: bool
    immutable_lineage_required: bool
    auditability_required: bool
    configured_memory_domains: tuple[str, ...]
    persistent_memory_enabled: bool
    learning_update_enabled: bool
    learner_execution_performed: bool
    memory_write_performed: bool
    database_access_performed: bool
    networking_performed: bool
    runtime_artifact_created: bool
    runtime_artifact_modified: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    foundation_ready: bool
    next_certification_authorized: bool
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

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise OracleMemoryLearnerFoundationInvariantError(
        "unsupported OML-001 value type: "
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


def verify_upstream_certification(
    certification: OracleMemoryLearnerUpstreamCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream certification hash mismatch"
        )

    if certification.upstream_subsystem_id != UPSTREAM_SUBSYSTEM_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream subsystem mismatch"
        )

    if certification.upstream_final_milestone != UPSTREAM_FINAL_MILESTONE:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream milestone mismatch"
        )

    if len(certification.upstream_report_hash) != 64:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream report hash invalid"
        )

    if len(certification.upstream_runner_sha256) != 64:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream runner hash invalid"
        )

    required_true = (
        certification.upstream_completed,
        certification.upstream_frozen,
        certification.upstream_production_ready,
        certification.upstream_read_only_boundary_frozen,
        certification.upstream_publication_disabled,
        certification.upstream_action_authorization_disabled,
        certification.upstream_qseries_execution_disabled,
        certification.downstream_subsystem_authorized,
    )

    if not all(required_true):
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream certification incomplete"
        )

    return True


def build_oracle_memory_learner_foundation_report(
    repository_root: str | Path,
    *,
    oit_final_freeze_report: OracleTerminalFinalFreezeCompletionReport,
) -> OracleMemoryLearnerFoundationReport:
    root = Path(repository_root).resolve()

    verify_oracle_terminal_final_freeze_completion_report(
        oit_final_freeze_report
    )

    freeze = oit_final_freeze_report.freeze_manifest

    if NEXT_SUBSYSTEM != SUBSYSTEM_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OIT-050 did not authorize the OML subsystem identity"
        )

    if freeze.subsystem_id != UPSTREAM_SUBSYSTEM_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OIT-050 frozen subsystem identity mismatch"
        )

    if freeze.final_milestone != UPSTREAM_FINAL_MILESTONE:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OIT-050 frozen milestone mismatch"
        )

    upstream_body = {
        "upstream_subsystem_id": freeze.subsystem_id,
        "upstream_final_milestone": freeze.final_milestone,
        "upstream_report_hash": oit_final_freeze_report.report_hash,
        "upstream_runner_sha256": freeze.source_runner_sha256,
        "upstream_completed": oit_final_freeze_report.subsystem_completed,
        "upstream_frozen": oit_final_freeze_report.subsystem_frozen,
        "upstream_production_ready": (
            oit_final_freeze_report.terminal_production_ready
        ),
        "upstream_read_only_boundary_frozen": (
            freeze.read_only_boundary_frozen
        ),
        "upstream_publication_disabled": (
            freeze.publication_frozen_disabled
        ),
        "upstream_action_authorization_disabled": (
            freeze.action_authorization_frozen_disabled
        ),
        "upstream_qseries_execution_disabled": (
            freeze.qseries_execution_frozen_disabled
        ),
        "downstream_subsystem_authorized": (
            oit_final_freeze_report.next_subsystem_authorized
        ),
    }

    upstream = OracleMemoryLearnerUpstreamCertification(
        **upstream_body,
        certification_hash=_stable_hash(upstream_body),
    )
    verify_upstream_certification(upstream)

    package_separate = (
        root / "qseries_v2" / "oracle_memory"
    ).resolve() != (
        root / "qseries_v2" / "oracle_terminal"
    ).resolve()

    ready = bool(
        package_separate
        and oit_final_freeze_report.subsystem_completed
        and oit_final_freeze_report.subsystem_frozen
        and oit_final_freeze_report.terminal_production_ready
        and oit_final_freeze_report.next_subsystem_authorized
        and freeze.read_only_boundary_frozen
        and freeze.publication_frozen_disabled
        and freeze.action_authorization_frozen_disabled
        and freeze.qseries_execution_frozen_disabled
    )

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "repository_root": str(root),
        "upstream_certification": upstream,
        "package_separate_from_oracle_terminal": package_separate,
        "certified_read_only_upstream_consumption_only": True,
        "deterministic_contract_enabled": True,
        "replay_verification_enabled": True,
        "immutable_lineage_required": True,
        "auditability_required": True,
        "configured_memory_domains": MEMORY_DOMAINS,
        "persistent_memory_enabled": False,
        "learning_update_enabled": False,
        "learner_execution_performed": False,
        "memory_write_performed": False,
        "database_access_performed": False,
        "networking_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "foundation_ready": ready,
        "next_certification_authorized": ready,
        "read_only": True,
        "failure_reason": (
            None
            if ready
            else "OML-001 foundation prerequisites not satisfied"
        ),
    }

    report = OracleMemoryLearnerFoundationReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_oracle_memory_learner_foundation_report(report)
    return report


def verify_oracle_memory_learner_foundation_report(
    report: OracleMemoryLearnerFoundationReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")

    if _stable_hash(body) != supplied:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 report hash mismatch"
        )

    if report.schema_version != SCHEMA_VERSION:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 schema mismatch"
        )

    if report.engine_id != ENGINE_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 engine mismatch"
        )

    if report.policy_id != POLICY_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 policy mismatch"
        )

    if report.subsystem_id != SUBSYSTEM_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 subsystem mismatch"
        )

    verify_upstream_certification(report.upstream_certification)

    if tuple(report.configured_memory_domains) != MEMORY_DOMAINS:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 memory-domain contract mismatch"
        )

    required_true = (
        report.package_separate_from_oracle_terminal,
        report.certified_read_only_upstream_consumption_only,
        report.deterministic_contract_enabled,
        report.replay_verification_enabled,
        report.immutable_lineage_required,
        report.auditability_required,
        report.foundation_ready,
        report.next_certification_authorized,
        report.read_only,
    )

    if not all(required_true):
        raise OracleMemoryLearnerFoundationInvariantError(
            report.failure_reason
            or "OML-001 required foundation guarantee missing"
        )

    forbidden = (
        report.persistent_memory_enabled,
        report.learning_update_enabled,
        report.learner_execution_performed,
        report.memory_write_performed,
        report.database_access_performed,
        report.networking_performed,
        report.runtime_artifact_created,
        report.runtime_artifact_modified,
        report.publication_allowed,
        report.action_authorization_allowed,
        report.qseries_execution_allowed,
    )

    if any(forbidden):
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 forbidden capability enabled"
        )

    if report.failure_reason is not None:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 ready report contains failure reason"
        )

    return True
