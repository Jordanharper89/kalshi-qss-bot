from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_final_freeze_readiness_certification_gate_078 import (
    NEXT_SUBSYSTEM,
    OracleMemoryFinalFreezeReadinessReport,
    verify_oracle_memory_final_freeze_readiness_report,
)

SCHEMA_VERSION = "OML-079"
ENGINE_ID = "OML-079"
POLICY_ID = "oracle-memory.final-freeze-and-completion-certification.v1"
UPSTREAM_SCHEMA_VERSION = "OML-078"
UPSTREAM_ENGINE_ID = "OML-078"
SUBSYSTEM_STATUS = "FROZEN"
STATE_READ_ONLY = "oracle_memory_final_frozen_read_only"
FINAL_FREEZE_MILESTONE = "OML-079"


class OracleMemoryFinalFreezeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryFinalFreezeCertificate:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    subsystem_status: str
    final_freeze_milestone: str
    next_subsystem: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    readiness_manifest_hash: str
    package_tree_hash: str
    test_tree_hash: str
    repository_tree_hash: str
    source_dependency_certification_hash: str
    source_dependency_memory_hash: str
    state: str
    repository_inventory_frozen: bool
    deterministic_replay_frozen: bool
    immutable_lineage_frozen: bool
    interface_contracts_frozen: bool
    oracle_terminal_separation_frozen: bool
    read_only_boundary_frozen: bool
    persistence_frozen_disabled: bool
    learning_updates_frozen_disabled: bool
    runtime_activation_frozen_disabled: bool
    publication_frozen_disabled: bool
    action_authorization_frozen_disabled: bool
    qseries_execution_frozen_disabled: bool
    further_oml_feature_builds_allowed: bool
    defect_corrections_only: bool
    universal_market_discovery_authorized: bool
    final_freeze_complete: bool
    read_only: bool
    certificate_hash: str


@dataclass(frozen=True)
class OracleMemoryFinalFreezeCompletion:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    subsystem_status: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    state: str
    certificate: OracleMemoryFinalFreezeCertificate
    final_freeze_complete: bool
    subsystem_completion_certified: bool
    downstream_universal_market_discovery_authorized: bool
    further_oml_feature_builds_allowed: bool
    defect_corrections_only: bool
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
    raise OracleMemoryFinalFreezeInvariantError(
        "unsupported OML-079 value type"
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


def _reject(reason: str) -> None:
    raise OracleMemoryFinalFreezeInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-079 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryFinalFreezeInvariantError(
            f"OML-079 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_final_freeze_completion(
    *,
    readiness: OracleMemoryFinalFreezeReadinessReport,
) -> OracleMemoryFinalFreezeCompletion:
    verify_oracle_memory_final_freeze_readiness_report(readiness)

    if readiness.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-079 upstream schema mismatch")
    if readiness.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-079 upstream engine mismatch")
    if not readiness.final_freeze_ready:
        _reject("OML-079 readiness gate not ready")
    if not readiness.downstream_final_freeze_authorized:
        _reject("OML-079 final freeze not authorized")
    if readiness.further_feature_builds_allowed:
        _reject("OML-079 upstream permits further feature builds")
    if not readiness.correction_builds_allowed_only_for_defects:
        _reject("OML-079 defect-only correction policy missing")
    if not readiness.read_only:
        _reject("OML-079 readiness report not read-only")
    if readiness.manifest.next_subsystem != NEXT_SUBSYSTEM:
        _reject("OML-079 next subsystem mismatch")
    if readiness.manifest.final_freeze_milestone != FINAL_FREEZE_MILESTONE:
        _reject("OML-079 final freeze milestone mismatch")

    certificate_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "subsystem_status": SUBSYSTEM_STATUS,
        "final_freeze_milestone": FINAL_FREEZE_MILESTONE,
        "next_subsystem": NEXT_SUBSYSTEM,
        "upstream_schema_version": readiness.schema_version,
        "upstream_engine_id": readiness.engine_id,
        "upstream_certification_hash": readiness.certification_hash,
        "readiness_manifest_hash": readiness.manifest.manifest_hash,
        "package_tree_hash": readiness.manifest.package_tree_hash,
        "test_tree_hash": readiness.manifest.test_tree_hash,
        "repository_tree_hash": readiness.manifest.repository_tree_hash,
        "source_dependency_certification_hash": (
            readiness.manifest.source_dependency_certification_hash
        ),
        "source_dependency_memory_hash": (
            readiness.manifest.source_dependency_memory_hash
        ),
        "state": STATE_READ_ONLY,
        "repository_inventory_frozen": True,
        "deterministic_replay_frozen": True,
        "immutable_lineage_frozen": True,
        "interface_contracts_frozen": True,
        "oracle_terminal_separation_frozen": True,
        "read_only_boundary_frozen": True,
        "persistence_frozen_disabled": True,
        "learning_updates_frozen_disabled": True,
        "runtime_activation_frozen_disabled": True,
        "publication_frozen_disabled": True,
        "action_authorization_frozen_disabled": True,
        "qseries_execution_frozen_disabled": True,
        "further_oml_feature_builds_allowed": False,
        "defect_corrections_only": True,
        "universal_market_discovery_authorized": True,
        "final_freeze_complete": True,
        "read_only": True,
    }
    certificate = OracleMemoryFinalFreezeCertificate(
        **certificate_body,
        certificate_hash=_stable_hash(certificate_body),
    )
    verify_oracle_memory_final_freeze_certificate(certificate)

    completion_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "subsystem_status": SUBSYSTEM_STATUS,
        "upstream_schema_version": readiness.schema_version,
        "upstream_engine_id": readiness.engine_id,
        "upstream_certification_hash": readiness.certification_hash,
        "state": STATE_READ_ONLY,
        "certificate": certificate,
        "final_freeze_complete": True,
        "subsystem_completion_certified": True,
        "downstream_universal_market_discovery_authorized": True,
        "further_oml_feature_builds_allowed": False,
        "defect_corrections_only": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "read_only": True,
    }
    completion = OracleMemoryFinalFreezeCompletion(
        **completion_body,
        certification_hash=_stable_hash(completion_body),
    )
    verify_oracle_memory_final_freeze_completion(completion)
    return completion


def verify_oracle_memory_final_freeze_certificate(
    certificate: OracleMemoryFinalFreezeCertificate,
) -> bool:
    body = asdict(certificate)
    supplied = body.pop("certificate_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-079 certificate hash mismatch")

    if certificate.schema_version != SCHEMA_VERSION:
        _reject("OML-079 certificate schema mismatch")
    if certificate.engine_id != ENGINE_ID:
        _reject("OML-079 certificate engine mismatch")
    if certificate.policy_id != POLICY_ID:
        _reject("OML-079 certificate policy mismatch")
    if certificate.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-079 certificate subsystem mismatch")
    if certificate.subsystem_status != SUBSYSTEM_STATUS:
        _reject("OML-079 subsystem not frozen")
    if certificate.final_freeze_milestone != FINAL_FREEZE_MILESTONE:
        _reject("OML-079 milestone mismatch")
    if certificate.next_subsystem != NEXT_SUBSYSTEM:
        _reject("OML-079 next subsystem mismatch")
    if certificate.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-079 certificate upstream schema mismatch")
    if certificate.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-079 certificate upstream engine mismatch")
    if certificate.state != STATE_READ_ONLY:
        _reject("OML-079 certificate state mismatch")

    for value in (
        certificate.upstream_certification_hash,
        certificate.readiness_manifest_hash,
        certificate.package_tree_hash,
        certificate.test_tree_hash,
        certificate.repository_tree_hash,
        certificate.source_dependency_certification_hash,
        certificate.source_dependency_memory_hash,
        certificate.certificate_hash,
    ):
        _require_hash(value, "certificate hash")

    required = (
        certificate.repository_inventory_frozen,
        certificate.deterministic_replay_frozen,
        certificate.immutable_lineage_frozen,
        certificate.interface_contracts_frozen,
        certificate.oracle_terminal_separation_frozen,
        certificate.read_only_boundary_frozen,
        certificate.persistence_frozen_disabled,
        certificate.learning_updates_frozen_disabled,
        certificate.runtime_activation_frozen_disabled,
        certificate.publication_frozen_disabled,
        certificate.action_authorization_frozen_disabled,
        certificate.qseries_execution_frozen_disabled,
        certificate.defect_corrections_only,
        certificate.universal_market_discovery_authorized,
        certificate.final_freeze_complete,
        certificate.read_only,
    )
    if not all(required):
        _reject("OML-079 certificate guarantee missing")
    if certificate.further_oml_feature_builds_allowed:
        _reject("OML-079 certificate permits further OML feature builds")
    return True


def verify_oracle_memory_final_freeze_completion(
    completion: OracleMemoryFinalFreezeCompletion,
) -> bool:
    body = asdict(completion)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-079 completion hash mismatch")

    if completion.schema_version != SCHEMA_VERSION:
        _reject("OML-079 schema mismatch")
    if completion.engine_id != ENGINE_ID:
        _reject("OML-079 engine mismatch")
    if completion.policy_id != POLICY_ID:
        _reject("OML-079 policy mismatch")
    if completion.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-079 subsystem mismatch")
    if completion.subsystem_status != SUBSYSTEM_STATUS:
        _reject("OML-079 completion status mismatch")
    if completion.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-079 upstream schema mismatch")
    if completion.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-079 upstream engine mismatch")
    if completion.state != STATE_READ_ONLY:
        _reject("OML-079 state mismatch")

    _require_hash(
        completion.upstream_certification_hash,
        "upstream certification hash",
    )
    _require_hash(completion.certification_hash, "completion hash")
    verify_oracle_memory_final_freeze_certificate(completion.certificate)

    if completion.upstream_certification_hash != (
        completion.certificate.upstream_certification_hash
    ):
        _reject("OML-079 upstream lineage mismatch")

    required = (
        completion.final_freeze_complete,
        completion.subsystem_completion_certified,
        completion.downstream_universal_market_discovery_authorized,
        completion.defect_corrections_only,
        completion.read_only,
    )
    if not all(required):
        _reject("OML-079 completion guarantee missing")
    if completion.further_oml_feature_builds_allowed:
        _reject("OML-079 permits further OML feature builds")

    forbidden = (
        completion.persistence_enabled,
        completion.learning_updates_enabled,
        completion.runtime_activation_enabled,
        completion.publication_enabled,
        completion.action_authorization_enabled,
        completion.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-079 forbidden capability enabled")
    return True
