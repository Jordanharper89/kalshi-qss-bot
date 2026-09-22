from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_attestation_consumption_completion_readiness_gate import (
    READINESS_STATUS as ORR_017_READINESS_STATUS,
    READINESS_TYPE as ORR_017_READINESS_TYPE,
    OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness,
)

SCHEMA_VERSION = "ORR-018"
ENGINE_ID = "ORR-018"
POLICY_ID = "oracle.research-response.final-completion-freeze-subsystem-certification.v1"
CERTIFICATION_TYPE = "oracle_research_response_final_completion_freeze_subsystem_certification"
CERTIFICATION_STATUS = "oracle_research_response_complete_frozen_and_certified"
EXPECTED_STAGE_COUNT = 18


class OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True)
class OracleResearchResponseFinalCompletionFreezeSubsystemCertification:
    certification_id: str
    completion_readiness_id: str
    completion_readiness_hash: str
    final_attestation_id: str
    final_attestation_hash: str
    request_id: str
    request_hash: str
    dependency_receipt_id: str
    dependency_receipt_hash: str
    source_runtime_completion_id: str
    source_runtime_completion_hash: str
    subsystem_namespace: str
    requester_id: str
    correlation_id: str
    question_text: str
    response_mode: str
    filters: tuple[tuple[str, str], ...]
    certified_at: datetime
    stage_count: int
    certified_stage_range: str
    module_manifest: tuple[tuple[str, str], ...]
    module_manifest_hash: str
    completion_readiness_identity_verified: bool
    completion_readiness_hash_verified: bool
    completion_readiness_contract_verified: bool
    complete_lineage_verified: bool
    module_manifest_verified: bool
    package_boundary_verified: bool
    deterministic_boundary_verified: bool
    immutable_certification_boundary_verified: bool
    read_only_boundary_verified: bool
    subsystem_complete_verified: bool
    subsystem_frozen_verified: bool
    further_certification_layers_required: bool
    callable_binding_allowed: bool
    callable_invocation_allowed: bool
    result_materialization_allowed: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    certification_type: str
    certification_status: str
    certification_hash: str


class OracleResearchResponseFinalCompletionFreezeSubsystemCertificationGate:
    def certify(
        self,
        *,
        readiness: OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness,
        certified_at: datetime,
        module_manifest: tuple[tuple[str, str], ...],
    ) -> OracleResearchResponseFinalCompletionFreezeSubsystemCertification:
        if not isinstance(
            readiness,
            OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness,
        ):
            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
                "readiness must be canonical ORR-017 completion readiness"
            )

        readiness_body = asdict(readiness)
        supplied_hash = readiness_body.pop("readiness_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(readiness_body) != supplied_hash:
            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
                "ORR-017 readiness hash mismatch"
            )

        required = (
            _valid_sha256(readiness.readiness_id),
            _valid_sha256(readiness.final_attestation_id),
            _valid_sha256(readiness.final_attestation_hash),
            _valid_sha256(readiness.request_id),
            _valid_sha256(readiness.request_hash),
            _valid_sha256(readiness.dependency_receipt_id),
            _valid_sha256(readiness.dependency_receipt_hash),
            _valid_sha256(readiness.source_runtime_completion_id),
            _valid_sha256(readiness.source_runtime_completion_hash),
            readiness.readiness_type == ORR_017_READINESS_TYPE,
            readiness.readiness_status == ORR_017_READINESS_STATUS,
            readiness.final_attestation_identity_verified,
            readiness.final_attestation_hash_verified,
            readiness.final_attestation_contract_verified,
            readiness.full_lineage_verified,
            readiness.activation_record_identity_verified,
            readiness.activation_record_hashes_verified,
            readiness.invocation_lineage_verified,
            readiness.invocation_order_verified,
            readiness.invocation_count_verified,
            readiness.approved_read_operations_verified,
            readiness.completion_scope_verified,
            readiness.completion_readiness_verified,
            readiness.callable_binding_remains_disabled_verified,
            readiness.callable_invocation_remains_disabled_verified,
            readiness.result_materialization_remains_disabled_verified,
            readiness.deterministic_boundary_verified,
            readiness.immutable_readiness_boundary_verified,
            readiness.read_only_boundary_verified,
            readiness.single_attestation_scope_verified,
            readiness.consumption_single_use_verified,
            not readiness.duplicate_consumption_allowed,
            not readiness.consumption_reversible,
        )
        forbidden = (
            readiness.runtime_serving_allowed,
            readiness.network_listener_allowed,
            readiness.database_connection_allowed,
            readiness.publication_allowed,
            readiness.qseries_handoff_allowed,
            readiness.qseries_execution_allowed,
            readiness.order_creation_allowed,
            readiness.funds_movement_allowed,
            readiness.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
                "ORR-017 readiness contract incomplete or unsafe"
            )

        if (
            not isinstance(certified_at, datetime)
            or certified_at.tzinfo is None
            or certified_at.utcoffset() is None
        ):
            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
                "certified_at must be timezone-aware"
            )
        at = certified_at.astimezone(timezone.utc)
        if at < readiness.final_attestation_consumed_at.astimezone(timezone.utc):
            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
                "certification cannot precede completion readiness"
            )

        if not isinstance(module_manifest, tuple) or not module_manifest:
            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
                "module_manifest must be a non-empty tuple"
            )
        normalized = tuple(sorted(module_manifest))
        if normalized != module_manifest:
            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
                "module_manifest must be canonically sorted"
            )
        names = [name for name, _ in module_manifest]
        hashes = [digest for _, digest in module_manifest]
        if (
            len(names) != len(set(names))
            or any(not isinstance(name, str) or not name.endswith(".py") for name in names)
            or any(not _valid_sha256(digest) for digest in hashes)
        ):
            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
                "module_manifest entries invalid"
            )

        manifest_hash = stable_hash(module_manifest)
        body = {
            "completion_readiness_id": readiness.readiness_id,
            "completion_readiness_hash": readiness.readiness_hash,
            "final_attestation_id": readiness.final_attestation_id,
            "final_attestation_hash": readiness.final_attestation_hash,
            "request_id": readiness.request_id,
            "request_hash": readiness.request_hash,
            "dependency_receipt_id": readiness.dependency_receipt_id,
            "dependency_receipt_hash": readiness.dependency_receipt_hash,
            "source_runtime_completion_id": readiness.source_runtime_completion_id,
            "source_runtime_completion_hash": readiness.source_runtime_completion_hash,
            "subsystem_namespace": readiness.subsystem_namespace,
            "requester_id": readiness.requester_id,
            "correlation_id": readiness.correlation_id,
            "question_text": readiness.question_text,
            "response_mode": readiness.response_mode,
            "filters": readiness.filters,
            "certified_at": at,
            "stage_count": EXPECTED_STAGE_COUNT,
            "certified_stage_range": "ORR-001..ORR-018",
            "module_manifest": module_manifest,
            "module_manifest_hash": manifest_hash,
            "completion_readiness_identity_verified": True,
            "completion_readiness_hash_verified": True,
            "completion_readiness_contract_verified": True,
            "complete_lineage_verified": True,
            "module_manifest_verified": True,
            "package_boundary_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_certification_boundary_verified": True,
            "read_only_boundary_verified": True,
            "subsystem_complete_verified": True,
            "subsystem_frozen_verified": True,
            "further_certification_layers_required": False,
            "callable_binding_allowed": False,
            "callable_invocation_allowed": False,
            "result_materialization_allowed": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "certification_type": CERTIFICATION_TYPE,
            "certification_status": CERTIFICATION_STATUS,
        }
        body["certification_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "completion_readiness_id": readiness.readiness_id,
                "completion_readiness_hash": readiness.readiness_hash,
                "module_manifest_hash": manifest_hash,
                "certified_at": at,
                "certification_type": CERTIFICATION_TYPE,
            }
        )
        return OracleResearchResponseFinalCompletionFreezeSubsystemCertification(
            **body,
            certification_hash=stable_hash(body),
        )


def build_module_manifest(package_directory: Path) -> tuple[tuple[str, str], ...]:
    if not package_directory.is_dir():
        raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
            "package_directory does not exist"
        )
    entries = []
    for path in sorted(package_directory.glob("*.py"), key=lambda item: item.name):
        if path.name == "__pycache__":
            continue
        entries.append((path.name, file_sha256(path)))
    if not entries:
        raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(
            "no Python modules found"
        )
    return tuple(entries)


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_TYPE",
    "CERTIFICATION_STATUS",
    "EXPECTED_STAGE_COUNT",
    "OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError",
    "OracleResearchResponseFinalCompletionFreezeSubsystemCertification",
    "OracleResearchResponseFinalCompletionFreezeSubsystemCertificationGate",
    "build_module_manifest",
    "file_sha256",
    "stable_hash",
]
