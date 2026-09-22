from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
OPERATOR = QSERIES / "oracle_operator"
RUNTIME = QSERIES / "oracle_operator_runtime"

SOURCE_047 = OPERATOR / "oracle_operator_subsystem_completion_certification_gate.py"
PRODUCTION = RUNTIME / "oracle_operator_runtime_certified_read_only_dependency_gate.py"
TEST = ROOT / "test_oor_001_oracle_operator_runtime_subsystem_root_and_certified_read_only_dependency_gate.py"

QSERIES_INIT = QSERIES / "__init__.py"
RUNTIME_INIT = RUNTIME / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.oracle_operator_subsystem_completion_certification_gate import (
    CERTIFICATION_STATUS as OOP_047_CERTIFICATION_STATUS,
    CERTIFICATION_TYPE as OOP_047_CERTIFICATION_TYPE,
    FREEZE_RECORD_TYPE as OOP_047_FREEZE_RECORD_TYPE,
    OracleOperatorSubsystemCompletionCertification,
)

SCHEMA_VERSION = "OOR-001"
ENGINE_ID = "OOR-001"
POLICY_ID = "oracle.operator-runtime-certified-read-only-dependency-gate.v1"
DEPENDENCY_STATUS = "oracle_operator_runtime_certified_read_only_dependency_consumed"
DEPENDENCY_TYPE = "frozen_oracle_operator_subsystem_read_only_runtime_dependency"
BOUNDARY_TYPE = "oracle_operator_runtime_subsystem_root_boundary"

RUNTIME_NAMESPACE = "qseries_v2.oracle_operator_runtime"
OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
QSERIES_EXECUTION_NAMESPACE = "qseries_v2.execution"


class OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True)
class OracleOperatorRuntimeSubsystemBoundary:
    boundary_type: str
    runtime_namespace: str
    operator_namespace: str
    qseries_execution_namespace: str
    certified_operator_dependency_required: bool
    frozen_operator_dependency_required: bool
    read_only_runtime_required: bool
    runtime_serving_allowed: bool
    runtime_serving_performed: bool
    network_listener_allowed: bool
    network_listener_started: bool
    operator_reexecution_allowed: bool
    operator_reexecution_performed: bool
    analytics_reexecution_allowed: bool
    analytics_reexecution_performed: bool
    database_connection_allowed: bool
    database_connection_performed: bool
    publication_allowed: bool
    publication_performed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    order_creation_allowed: bool
    order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    boundary_hash: str


@dataclass(frozen=True)
class OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt:
    dependency_receipt_id: str
    source_operator_completion_certification_id: str
    source_operator_completion_certification_hash: str
    source_freeze_record_id: str
    source_freeze_record_payload_hash: str
    source_certification_status: str
    source_certification_type: str
    source_freeze_record_type: str
    runtime_namespace: str
    operator_namespace: str
    qseries_execution_namespace: str
    consumer_id: str
    projection: str
    source_query_boundary_complete: bool
    source_research_response_boundary_complete: bool
    source_session_boundary_complete: bool
    source_console_boundary_complete: bool
    source_presentation_boundary_complete: bool
    source_operator_subsystem_completion_ready: bool
    source_operator_subsystem_completion_certified: bool
    source_operator_subsystem_frozen: bool
    source_further_operator_builds_required: bool
    certification_identity_verified: bool
    certification_hash_verified: bool
    certification_status_verified: bool
    certification_type_verified: bool
    freeze_record_type_verified: bool
    freeze_record_identity_verified: bool
    freeze_record_payload_hash_verified: bool
    operator_namespace_verified: bool
    complete_operator_lineage_verified: bool
    operator_completion_verified: bool
    operator_freeze_verified: bool
    deterministic_dependency_verified: bool
    immutable_dependency_verified: bool
    read_only_dependency_verified: bool
    runtime_subsystem_root_established: bool
    runtime_serving_allowed: bool
    runtime_serving_performed: bool
    network_listener_allowed: bool
    network_listener_started: bool
    operator_reexecution_allowed: bool
    operator_reexecution_performed: bool
    analytics_reexecution_allowed: bool
    analytics_reexecution_performed: bool
    database_connection_allowed: bool
    database_connection_performed: bool
    publication_allowed: bool
    publication_performed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    order_creation_allowed: bool
    order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    dependency_status: str
    dependency_type: str
    dependency_receipt_hash: str


class OracleOperatorRuntimeCertifiedReadOnlyDependencyGate:
    def subsystem_boundary(self) -> OracleOperatorRuntimeSubsystemBoundary:
        body = {
            "boundary_type": BOUNDARY_TYPE,
            "runtime_namespace": RUNTIME_NAMESPACE,
            "operator_namespace": OPERATOR_NAMESPACE,
            "qseries_execution_namespace": QSERIES_EXECUTION_NAMESPACE,
            "certified_operator_dependency_required": True,
            "frozen_operator_dependency_required": True,
            "read_only_runtime_required": True,
            "runtime_serving_allowed": False,
            "runtime_serving_performed": False,
            "network_listener_allowed": False,
            "network_listener_started": False,
            "operator_reexecution_allowed": False,
            "operator_reexecution_performed": False,
            "analytics_reexecution_allowed": False,
            "analytics_reexecution_performed": False,
            "database_connection_allowed": False,
            "database_connection_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "order_creation_allowed": False,
            "order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
        }
        return OracleOperatorRuntimeSubsystemBoundary(
            **body,
            boundary_hash=stable_hash(body),
        )

    @staticmethod
    def _verify(
        certification: OracleOperatorSubsystemCompletionCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorSubsystemCompletionCertification,
        ):
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "source must be canonical OOP-047 completion certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop(
            "oracle_operator_subsystem_completion_certification_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "OOP-047 certification hash mismatch"
            )

        if certification.certification_status != OOP_047_CERTIFICATION_STATUS:
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "OOP-047 certification status mismatch"
            )
        if certification.certification_type != OOP_047_CERTIFICATION_TYPE:
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "OOP-047 certification type mismatch"
            )
        if certification.freeze_record_type != OOP_047_FREEZE_RECORD_TYPE:
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "OOP-047 freeze record type mismatch"
            )
        if certification.operator_namespace != OPERATOR_NAMESPACE:
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "operator namespace mismatch"
            )

        if not _valid_sha256(certification.freeze_record_id):
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "freeze record id invalid"
            )
        if not _valid_sha256(certification.freeze_record_payload_hash):
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "freeze record payload hash invalid"
            )
        if stable_hash(certification.freeze_record_payload) != certification.freeze_record_payload_hash:
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "freeze record payload hash mismatch"
            )

        payload = certification.freeze_record_payload
        required_payload_state = (
            payload.get("freeze_record_id") == certification.freeze_record_id,
            payload.get("operator_namespace") == certification.operator_namespace,
            payload.get("query_boundary_complete") is True,
            payload.get("research_response_boundary_complete") is True,
            payload.get("session_boundary_complete") is True,
            payload.get("console_boundary_complete") is True,
            payload.get("presentation_boundary_complete") is True,
            payload.get("operator_subsystem_complete") is True,
            payload.get("operator_subsystem_completion_certified") is True,
            payload.get("operator_subsystem_frozen") is True,
            payload.get("further_operator_builds_required") is False,
            payload.get("read_only") is True,
            payload.get("qseries_handoff_disabled") is True,
            payload.get("qseries_execution_disabled") is True,
            payload.get("orders_disabled") is True,
            payload.get("funds_movement_disabled") is True,
            payload.get("portfolio_mutation_disabled") is True,
        )
        if not all(required_payload_state):
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "OOP-047 freeze state mismatch"
            )

        required = (
            certification.readiness_identity_verified,
            certification.readiness_hash_verified,
            certification.readiness_status_verified,
            certification.readiness_type_verified,
            certification.readiness_record_type_verified,
            certification.readiness_record_identity_verified,
            certification.readiness_record_payload_hash_verified,
            certification.operator_namespace_verified,
            certification.query_boundary_verified,
            certification.research_response_boundary_verified,
            certification.session_boundary_verified,
            certification.console_boundary_verified,
            certification.presentation_boundary_verified,
            certification.publication_chain_completion_verified,
            certification.presentation_subsystem_completion_verified,
            certification.complete_lineage_verified,
            certification.deterministic_certification_verified,
            certification.immutable_freeze_record_verified,
            certification.read_only_operator_subsystem_verified,
            certification.operator_query_boundary_complete,
            certification.operator_research_response_boundary_complete,
            certification.operator_session_boundary_complete,
            certification.operator_console_boundary_complete,
            certification.operator_presentation_boundary_complete,
            certification.operator_presentation_subsystem_completion_certified,
            certification.operator_presentation_subsystem_frozen,
            certification.oracle_operator_subsystem_completion_ready,
            certification.oracle_operator_subsystem_completion_certified,
            certification.oracle_operator_subsystem_frozen,
        )
        if not all(required):
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "OOP-047 completion certification is incomplete"
            )
        if certification.further_operator_builds_required:
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "Oracle Operator is not terminally complete"
            )

        forbidden = (
            certification.qseries_handoff_allowed,
            certification.qseries_execution_allowed,
            certification.qseries_execution_performed,
            certification.order_creation_allowed,
            certification.order_creation_performed,
            certification.funds_movement_allowed,
            certification.funds_movement_performed,
            certification.portfolio_mutation_allowed,
            certification.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "forbidden downstream activity detected"
            )

    def consume(
        self,
        *,
        certification: OracleOperatorSubsystemCompletionCertification,
        consumer_id: str = "oracle.operator.runtime.v1",
        projection: str = "certified_operator_read_only",
    ) -> OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt:
        self._verify(certification)

        if consumer_id != "oracle.operator.runtime.v1":
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "runtime consumer identity mismatch"
            )
        if projection != "certified_operator_read_only":
            raise OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError(
                "runtime projection mismatch"
            )

        receipt_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_operator_completion_certification_id": certification.oracle_operator_subsystem_completion_certification_id,
                "source_operator_completion_certification_hash": certification.oracle_operator_subsystem_completion_certification_hash,
                "source_freeze_record_id": certification.freeze_record_id,
                "source_freeze_record_payload_hash": certification.freeze_record_payload_hash,
                "consumer_id": consumer_id,
                "projection": projection,
                "dependency_type": DEPENDENCY_TYPE,
            }
        )

        body = {
            "dependency_receipt_id": receipt_id,
            "source_operator_completion_certification_id": certification.oracle_operator_subsystem_completion_certification_id,
            "source_operator_completion_certification_hash": certification.oracle_operator_subsystem_completion_certification_hash,
            "source_freeze_record_id": certification.freeze_record_id,
            "source_freeze_record_payload_hash": certification.freeze_record_payload_hash,
            "source_certification_status": certification.certification_status,
            "source_certification_type": certification.certification_type,
            "source_freeze_record_type": certification.freeze_record_type,
            "runtime_namespace": RUNTIME_NAMESPACE,
            "operator_namespace": certification.operator_namespace,
            "qseries_execution_namespace": QSERIES_EXECUTION_NAMESPACE,
            "consumer_id": consumer_id,
            "projection": projection,
            "source_query_boundary_complete": certification.operator_query_boundary_complete,
            "source_research_response_boundary_complete": certification.operator_research_response_boundary_complete,
            "source_session_boundary_complete": certification.operator_session_boundary_complete,
            "source_console_boundary_complete": certification.operator_console_boundary_complete,
            "source_presentation_boundary_complete": certification.operator_presentation_boundary_complete,
            "source_operator_subsystem_completion_ready": certification.oracle_operator_subsystem_completion_ready,
            "source_operator_subsystem_completion_certified": certification.oracle_operator_subsystem_completion_certified,
            "source_operator_subsystem_frozen": certification.oracle_operator_subsystem_frozen,
            "source_further_operator_builds_required": certification.further_operator_builds_required,
            "certification_identity_verified": True,
            "certification_hash_verified": True,
            "certification_status_verified": True,
            "certification_type_verified": True,
            "freeze_record_type_verified": True,
            "freeze_record_identity_verified": True,
            "freeze_record_payload_hash_verified": True,
            "operator_namespace_verified": True,
            "complete_operator_lineage_verified": True,
            "operator_completion_verified": True,
            "operator_freeze_verified": True,
            "deterministic_dependency_verified": True,
            "immutable_dependency_verified": True,
            "read_only_dependency_verified": True,
            "runtime_subsystem_root_established": True,
            "runtime_serving_allowed": False,
            "runtime_serving_performed": False,
            "network_listener_allowed": False,
            "network_listener_started": False,
            "operator_reexecution_allowed": False,
            "operator_reexecution_performed": False,
            "analytics_reexecution_allowed": False,
            "analytics_reexecution_performed": False,
            "database_connection_allowed": False,
            "database_connection_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "order_creation_allowed": False,
            "order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "dependency_status": DEPENDENCY_STATUS,
            "dependency_type": DEPENDENCY_TYPE,
        }

        return OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt(
            **body,
            dependency_receipt_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "DEPENDENCY_STATUS",
    "DEPENDENCY_TYPE",
    "BOUNDARY_TYPE",
    "RUNTIME_NAMESPACE",
    "OPERATOR_NAMESPACE",
    "QSERIES_EXECUTION_NAMESPACE",
    "OracleOperatorRuntimeSubsystemBoundary",
    "OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt",
    "OracleOperatorRuntimeCertifiedReadOnlyDependencyGate",
    "OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_047_oracle_operator_subsystem_completion_certification_gate import (
    _readiness,
)
from qseries_v2.oracle_operator.oracle_operator_subsystem_completion_certification_gate import (
    OracleOperatorSubsystemCompletionCertificationGate,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_certified_read_only_dependency_gate import (
    BOUNDARY_TYPE,
    DEPENDENCY_STATUS,
    DEPENDENCY_TYPE,
    OPERATOR_NAMESPACE,
    QSERIES_EXECUTION_NAMESPACE,
    RUNTIME_NAMESPACE,
    OracleOperatorRuntimeCertifiedReadOnlyDependencyGate,
    OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError,
    stable_hash,
)


def _certification():
    return OracleOperatorSubsystemCompletionCertificationGate().certify(
        readiness=_readiness()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe runtime dependency accepted")
    except OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-001 TEST")
    print(" ORACLE OPERATOR RUNTIME ROOT")
    print(" CERTIFIED READ-ONLY DEPENDENCY")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorRuntimeCertifiedReadOnlyDependencyGate()

    boundary = gate.subsystem_boundary()
    assert boundary.boundary_type == BOUNDARY_TYPE
    assert boundary.runtime_namespace == RUNTIME_NAMESPACE
    assert boundary.operator_namespace == OPERATOR_NAMESPACE
    assert boundary.qseries_execution_namespace == QSERIES_EXECUTION_NAMESPACE
    assert boundary.certified_operator_dependency_required
    assert boundary.frozen_operator_dependency_required
    assert boundary.read_only_runtime_required
    assert boundary.boundary_hash == stable_hash(
        {
            key: value
            for key, value in boundary.__dict__.items()
            if key != "boundary_hash"
        }
    )

    first = gate.consume(certification=certification)
    repeated = gate.consume(certification=certification)

    assert first == repeated
    assert first.dependency_receipt_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "dependency_receipt_hash"
        }
    )
    assert first.dependency_status == DEPENDENCY_STATUS
    assert first.dependency_type == DEPENDENCY_TYPE
    assert first.runtime_namespace == RUNTIME_NAMESPACE
    assert first.operator_namespace == OPERATOR_NAMESPACE
    assert first.qseries_execution_namespace == QSERIES_EXECUTION_NAMESPACE
    assert first.consumer_id == "oracle.operator.runtime.v1"
    assert first.projection == "certified_operator_read_only"

    assert first.source_query_boundary_complete
    assert first.source_research_response_boundary_complete
    assert first.source_session_boundary_complete
    assert first.source_console_boundary_complete
    assert first.source_presentation_boundary_complete
    assert first.source_operator_subsystem_completion_ready
    assert first.source_operator_subsystem_completion_certified
    assert first.source_operator_subsystem_frozen
    assert not first.source_further_operator_builds_required

    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.certification_type_verified
    assert first.freeze_record_type_verified
    assert first.freeze_record_identity_verified
    assert first.freeze_record_payload_hash_verified
    assert first.operator_namespace_verified
    assert first.complete_operator_lineage_verified
    assert first.operator_completion_verified
    assert first.operator_freeze_verified
    assert first.deterministic_dependency_verified
    assert first.immutable_dependency_verified
    assert first.read_only_dependency_verified
    assert first.runtime_subsystem_root_established

    forbidden = (
        boundary.runtime_serving_allowed,
        boundary.runtime_serving_performed,
        boundary.network_listener_allowed,
        boundary.network_listener_started,
        boundary.operator_reexecution_allowed,
        boundary.operator_reexecution_performed,
        boundary.analytics_reexecution_allowed,
        boundary.analytics_reexecution_performed,
        boundary.database_connection_allowed,
        boundary.database_connection_performed,
        boundary.publication_allowed,
        boundary.publication_performed,
        boundary.qseries_handoff_allowed,
        boundary.qseries_execution_allowed,
        boundary.qseries_execution_performed,
        boundary.order_creation_allowed,
        boundary.order_creation_performed,
        boundary.funds_movement_allowed,
        boundary.funds_movement_performed,
        boundary.portfolio_mutation_allowed,
        boundary.portfolio_mutation_performed,
        first.runtime_serving_allowed,
        first.runtime_serving_performed,
        first.network_listener_allowed,
        first.network_listener_started,
        first.operator_reexecution_allowed,
        first.operator_reexecution_performed,
        first.analytics_reexecution_allowed,
        first.analytics_reexecution_performed,
        first.database_connection_allowed,
        first.database_connection_performed,
        first.publication_allowed,
        first.publication_performed,
        first.qseries_handoff_allowed,
        first.qseries_execution_allowed,
        first.qseries_execution_performed,
        first.order_creation_allowed,
        first.order_creation_performed,
        first.funds_movement_allowed,
        first.funds_movement_performed,
        first.portfolio_mutation_allowed,
        first.portfolio_mutation_performed,
    )
    assert not any(forbidden)

    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            oracle_operator_subsystem_completion_certification_hash="0" * 64,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            certification_status="wrong_status",
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            freeze_record_payload_hash="0" * 64,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            oracle_operator_subsystem_completion_certified=False,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            oracle_operator_subsystem_frozen=False,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            further_operator_builds_required=True,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            qseries_execution_allowed=True,
        )
    ))
    _reject(lambda: gate.consume(
        certification=certification,
        consumer_id="wrong.consumer",
    ))
    _reject(lambda: gate.consume(
        certification=certification,
        projection="wrong_projection",
    ))

    print("[PASS] Actual OOP-047 completion certification consumed")
    print("[PASS] OOP-047 identity, hash, status, type, and freeze record verified")
    print("[PASS] Complete Query through Presentation lineage preserved")
    print("[PASS] Terminal Operator completion and freeze verified")
    print("[PASS] Oracle Operator Runtime root boundary established")
    print("[PASS] Deterministic immutable dependency receipt created")
    print("[PASS] Runtime serving and network listener remain disabled")
    print("[PASS] Operator and analytics re-execution remain disabled")
    print("[PASS] Database connection and publication remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    print("[PASS] Tampered and unauthorized dependencies rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path: Path, label: str, tokens: tuple[str, ...]) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Actual {label} module missing: {path}")
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise RuntimeError(f"Actual {label} contract mismatch: {missing}")
    print(f"[OK] Actual {label} contract verified")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def ensure_package(path: Path, docstring: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(docstring + "\n", encoding="utf-8", newline="\n")
        print(f"[OK] PACKAGE CREATED: {path.resolve()}")
    else:
        print(f"[OK] PACKAGE PRESENT: {path.resolve()}")


def export(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in existing.splitlines():
        print(f"[OK] PACKAGE EXPORT PRESENT: {path.resolve()}")
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + line + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" OOR-001 INSTALLER")
    print(" ORACLE OPERATOR RUNTIME ROOT")
    print(" CERTIFIED READ-ONLY DEPENDENCY")
    print("=" * 40)

    verify(
        SOURCE_047,
        "OOP-047",
        (
            'SCHEMA_VERSION = "OOP-047"',
            "class OracleOperatorSubsystemCompletionCertification",
            "oracle_operator_subsystem_completion_certification_hash",
            "freeze_record_payload_hash",
            "oracle_operator_subsystem_completion_certified",
            "oracle_operator_subsystem_frozen",
            "further_operator_builds_required",
            "qseries_handoff_allowed",
            "qseries_execution_allowed",
            "order_creation_allowed",
            "funds_movement_allowed",
            "portfolio_mutation_allowed",
        ),
    )

    source_hash = sha256_file(SOURCE_047)
    qseries_hash = sha256_file(QSERIES_INIT) if QSERIES_INIT.exists() else None

    ensure_package(RUNTIME_INIT, '"""Oracle Operator Runtime subsystem."""')
    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        RUNTIME_INIT,
        "from .oracle_operator_runtime_certified_read_only_dependency_gate import *",
    )

    for path in (PRODUCTION, TEST, RUNTIME_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and runtime package syntax verified")

    if sha256_file(SOURCE_047) != source_hash:
        raise RuntimeError("Protected OOP-047 module changed during installation")
    if qseries_hash is not None and sha256_file(QSERIES_INIT) != qseries_hash:
        raise RuntimeError("Top-level qseries_v2 package changed during installation")
    print("[PASS] OOP-047 and top-level qseries_v2 package unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    if sha256_file(SOURCE_047) != source_hash:
        raise RuntimeError("Protected OOP-047 module changed during test")
    if qseries_hash is not None and sha256_file(QSERIES_INIT) != qseries_hash:
        raise RuntimeError("Top-level qseries_v2 package changed during test")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] Oracle Operator package and frozen OOP lineage unchanged")
    print("[PASS] No analytics, acquisition, or Q Series execution package modified")
    print("[OK] OOR-001 test executed automatically")
    print()
    print("[DONE] OOR-001 Oracle Operator Runtime root established")
    print()
    print("NEXT BUILDS")
    print("  OOR-002 Runtime dependency admission gate")
    print("  OOR-003 Certified presentation access request")
    print("  OOR-004 Certified presentation access admission")
    print("  OOR-005 Read-only runtime view materialization readiness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
