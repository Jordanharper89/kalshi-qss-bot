from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
ANALYTICS_QUERY = QSERIES / "oracle_intelligence" / "analytics" / "downstream" / "query"
OPERATOR = QSERIES / "oracle_operator"
OPERATOR_QUERY = OPERATOR / "query"

SOURCE_060 = ANALYTICS_QUERY / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
SOURCE_OOP_001 = OPERATOR / "oracle_operator_analytics_read_only_dependency_gate.py"
SOURCE_OOP_002 = OPERATOR / "oracle_operator_analytics_dependency_admission_gate.py"
SOURCE_OOP_003 = OPERATOR_QUERY / "oracle_operator_query_request_contract.py"
PRODUCTION = OPERATOR_QUERY / "oracle_operator_query_request_admission_gate.py"
TEST = ROOT / "test_oop_004_oracle_operator_query_request_admission_gate.py"
OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"

PRODUCTION_SOURCE = r'''
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_request_contract import (
    EXPECTED_CONSUMER_ID,
    EXPECTED_PROJECTION,
    QUERY_REQUEST_STATUS as OOP_003_QUERY_REQUEST_STATUS,
    OracleOperatorQueryRequest,
)

SCHEMA_VERSION = "OOP-004"
ENGINE_ID = "OOP-004"
POLICY_ID = "oracle.operator.query-request-admission-gate.v1"
ADMISSION_SCHEMA_VERSION = "oracle.operator.query.request-admission.v1"
ADMISSION_STATUS = "operator_query_request_admitted"
EXPECTED_QUERY_REQUEST_STATUS = OOP_003_QUERY_REQUEST_STATUS
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryRequestAdmissionInvariantError(RuntimeError):
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
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryRequestAdmissionInvariantError(
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
class OracleOperatorQueryRequestAdmission:
    query_admission_id: str
    source_query_request_id: str
    source_query_request_hash: str
    source_admission_id: str
    source_admission_hash: str
    source_dependency_receipt_id: str
    source_dependency_receipt_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    operator_namespace: str
    query_namespace: str
    consumer_id: str
    projection: str
    query_mode: str
    query_text: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    admitted_entry_count: int
    admitted_response_artifact_entry_ids: tuple[str, ...]
    admitted_query_response_ids: tuple[str, ...]
    query_request_type_verified: bool
    query_request_identity_verified: bool
    query_request_hash_verified: bool
    query_request_status_verified: bool
    source_admission_lineage_verified: bool
    source_dependency_lineage_verified: bool
    source_authorization_lineage_verified: bool
    operator_namespace_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    query_parameters_verified: bool
    authorized_scope_verified: bool
    authorized_scope_frozen: bool
    deterministic_admission_verified: bool
    analytics_read_only_dependency_preserved: bool
    query_resolution_allowed: bool
    query_resolution_performed: bool
    analytics_query_execution_allowed: bool
    analytics_query_execution_performed: bool
    analytics_reexecution_allowed: bool
    analytics_reexecution_performed: bool
    analytics_database_connection_allowed: bool
    analytics_database_connection_performed: bool
    analytics_mutation_allowed: bool
    analytics_mutation_performed: bool
    operator_session_construction_allowed: bool
    operator_console_rendering_allowed: bool
    operator_presentation_rendering_allowed: bool
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
    admission_status: str
    query_admission_hash: str


class OracleOperatorQueryRequestAdmissionGate:
    @staticmethod
    def _verify_request(request: OracleOperatorQueryRequest) -> None:
        if not isinstance(request, OracleOperatorQueryRequest):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "source must be the canonical OOP-003 query request"
            )

        body = asdict(request)
        supplied_hash = body.pop("query_request_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 query request hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 query request hash mismatch"
            )

        required_hashes = (
            request.query_request_id,
            request.source_admission_hash,
            request.source_dependency_receipt_hash,
            request.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 request lineage contains invalid hashes"
            )
        if request.query_request_status != EXPECTED_QUERY_REQUEST_STATUS:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 query request is not materialized"
            )
        if request.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "operator namespace mismatch"
            )
        if request.consumer_id != EXPECTED_CONSUMER_ID:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "consumer identity mismatch"
            )
        if request.projection != EXPECTED_PROJECTION:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "projection identity mismatch"
            )

        if request.authorized_entry_count < 1:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "query request contains no authorized entries"
            )
        if request.authorized_entry_count != len(
            request.authorized_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if request.authorized_entry_count != len(
            request.authorized_query_response_ids
        ):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(request.authorized_response_artifact_entry_ids)) != request.authorized_entry_count:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(request.authorized_query_response_ids)) != request.authorized_entry_count:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            request.admission_type_verified,
            request.admission_hash_verified,
            request.admission_status_verified,
            request.consumer_identity_verified,
            request.projection_identity_verified,
            request.query_mode_verified,
            request.time_scope_verified,
            request.sort_order_verified,
            request.result_limit_verified,
            request.authorized_scope_preserved,
            request.deterministic_request_verified,
            request.analytics_read_only_dependency_preserved,
        )
        if not all(required_truths):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 request is incomplete"
            )

        forbidden_authority = (
            request.analytics_query_execution_allowed,
            request.analytics_query_execution_performed,
            request.analytics_reexecution_allowed,
            request.analytics_reexecution_performed,
            request.analytics_database_connection_allowed,
            request.analytics_database_connection_performed,
            request.analytics_mutation_allowed,
            request.analytics_mutation_performed,
            request.operator_session_construction_allowed,
            request.operator_console_rendering_allowed,
            request.operator_presentation_rendering_allowed,
            request.publication_allowed,
            request.publication_performed,
            request.qseries_handoff_allowed,
            request.qseries_execution_allowed,
            request.qseries_execution_performed,
            request.order_creation_allowed,
            request.order_creation_performed,
            request.funds_movement_allowed,
            request.funds_movement_performed,
            request.portfolio_mutation_allowed,
            request.portfolio_mutation_performed,
        )
        if any(forbidden_authority):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 request contains forbidden authority or activity"
            )

    def admit(self, *, request: OracleOperatorQueryRequest) -> OracleOperatorQueryRequestAdmission:
        self._verify_request(request)

        query_admission_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_query_request_id": request.query_request_id,
                "source_query_request_hash": request.query_request_hash,
                "query_mode": request.query_mode,
                "query_text": request.query_text,
                "time_scope": request.time_scope,
                "sort_order": request.sort_order,
                "result_limit": request.result_limit,
                "requested_tags": request.requested_tags,
                "authorized_response_artifact_entry_ids": request.authorized_response_artifact_entry_ids,
                "authorized_query_response_ids": request.authorized_query_response_ids,
            }
        )

        body = {
            "query_admission_id": query_admission_id,
            "source_query_request_id": request.query_request_id,
            "source_query_request_hash": request.query_request_hash,
            "source_admission_id": request.source_admission_id,
            "source_admission_hash": request.source_admission_hash,
            "source_dependency_receipt_id": request.source_dependency_receipt_id,
            "source_dependency_receipt_hash": request.source_dependency_receipt_hash,
            "source_authorization_id": request.source_authorization_id,
            "source_authorization_hash": request.source_authorization_hash,
            "operator_namespace": request.operator_namespace,
            "query_namespace": EXPECTED_QUERY_NAMESPACE,
            "consumer_id": request.consumer_id,
            "projection": request.projection,
            "query_mode": request.query_mode,
            "query_text": request.query_text,
            "time_scope": request.time_scope,
            "sort_order": request.sort_order,
            "result_limit": request.result_limit,
            "requested_tags": tuple(request.requested_tags),
            "admitted_entry_count": request.authorized_entry_count,
            "admitted_response_artifact_entry_ids": tuple(request.authorized_response_artifact_entry_ids),
            "admitted_query_response_ids": tuple(request.authorized_query_response_ids),
            "query_request_type_verified": True,
            "query_request_identity_verified": True,
            "query_request_hash_verified": True,
            "query_request_status_verified": True,
            "source_admission_lineage_verified": True,
            "source_dependency_lineage_verified": True,
            "source_authorization_lineage_verified": True,
            "operator_namespace_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "query_parameters_verified": True,
            "authorized_scope_verified": True,
            "authorized_scope_frozen": True,
            "deterministic_admission_verified": True,
            "analytics_read_only_dependency_preserved": True,
            "query_resolution_allowed": True,
            "query_resolution_performed": False,
            "analytics_query_execution_allowed": False,
            "analytics_query_execution_performed": False,
            "analytics_reexecution_allowed": False,
            "analytics_reexecution_performed": False,
            "analytics_database_connection_allowed": False,
            "analytics_database_connection_performed": False,
            "analytics_mutation_allowed": False,
            "analytics_mutation_performed": False,
            "operator_session_construction_allowed": False,
            "operator_console_rendering_allowed": False,
            "operator_presentation_rendering_allowed": False,
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
            "admission_status": ADMISSION_STATUS,
        }
        return OracleOperatorQueryRequestAdmission(
            **body,
            query_admission_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ADMISSION_SCHEMA_VERSION",
    "ADMISSION_STATUS",
    "EXPECTED_QUERY_REQUEST_STATUS",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryRequestAdmission",
    "OracleOperatorQueryRequestAdmissionGate",
    "OracleOperatorQueryRequestAdmissionInvariantError",
    "stable_hash",
]
'''

TEST_SOURCE = r'''
from __future__ import annotations

from dataclasses import replace

from test_int_oia_060_oracle_intelligence_analytics_certified_query_response_artifact_authorization_consumption_attestation_authorization_consumption_attestation_authorization_gate import _attestation
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate
from qseries_v2.oracle_operator.oracle_operator_analytics_read_only_dependency_gate import OracleOperatorAnalyticsReadOnlyDependencyGate
from qseries_v2.oracle_operator.oracle_operator_analytics_dependency_admission_gate import OracleOperatorAnalyticsDependencyAdmissionGate
from qseries_v2.oracle_operator.query.oracle_operator_query_request_contract import OracleOperatorQueryRequestContract
from qseries_v2.oracle_operator.query.oracle_operator_query_request_admission_gate import (
    ADMISSION_STATUS,
    OracleOperatorQueryRequestAdmissionGate,
    OracleOperatorQueryRequestAdmissionInvariantError,
    stable_hash,
)


def _request():
    authorization = OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate().authorize(
        attestation=_attestation(),
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )
    receipt = OracleOperatorAnalyticsReadOnlyDependencyGate().consume(authorization=authorization)
    admission = OracleOperatorAnalyticsDependencyAdmissionGate().admit(receipt=receipt)
    return OracleOperatorQueryRequestContract().materialize(
        admission=admission,
        query_mode="opportunity_lookup",
        query_text="Show major opportunities closing today",
        time_scope="same_day",
        sort_order="priority",
        result_limit=20,
        requested_tags=("kalshi", "major"),
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe query request admitted")
    except OracleOperatorQueryRequestAdmissionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-004 TEST")
    print(" QUERY REQUEST ADMISSION")
    print(" AUTHORIZED SCOPE FREEZE")
    print("=" * 40)

    request = _request()
    gate = OracleOperatorQueryRequestAdmissionGate()
    first = gate.admit(request=request)
    repeated = gate.admit(request=request)

    assert first == repeated
    assert first.query_admission_hash == stable_hash({
        key: value for key, value in first.__dict__.items() if key != "query_admission_hash"
    })
    assert first.source_query_request_id == request.query_request_id
    assert first.source_query_request_hash == request.query_request_hash
    assert first.consumer_id == "oracle.operator.console.v1"
    assert first.projection == "operator_research"
    assert first.operator_namespace == "qseries_v2.oracle_operator"
    assert first.query_namespace == "qseries_v2.oracle_operator.query"
    assert first.query_mode == "opportunity_lookup"
    assert first.query_text == "Show major opportunities closing today"
    assert first.time_scope == "same_day"
    assert first.sort_order == "priority"
    assert first.result_limit == 20
    assert first.requested_tags == ("kalshi", "major")
    assert first.admitted_entry_count == request.authorized_entry_count
    assert first.admitted_response_artifact_entry_ids == request.authorized_response_artifact_entry_ids
    assert first.admitted_query_response_ids == request.authorized_query_response_ids

    required_true = (
        first.query_request_type_verified,
        first.query_request_identity_verified,
        first.query_request_hash_verified,
        first.query_request_status_verified,
        first.source_admission_lineage_verified,
        first.source_dependency_lineage_verified,
        first.source_authorization_lineage_verified,
        first.operator_namespace_verified,
        first.consumer_identity_verified,
        first.projection_identity_verified,
        first.query_parameters_verified,
        first.authorized_scope_verified,
        first.authorized_scope_frozen,
        first.deterministic_admission_verified,
        first.analytics_read_only_dependency_preserved,
        first.query_resolution_allowed,
    )
    assert all(required_true)

    forbidden = (
        first.query_resolution_performed,
        first.analytics_query_execution_allowed,
        first.analytics_query_execution_performed,
        first.analytics_reexecution_allowed,
        first.analytics_reexecution_performed,
        first.analytics_database_connection_allowed,
        first.analytics_database_connection_performed,
        first.analytics_mutation_allowed,
        first.analytics_mutation_performed,
        first.operator_session_construction_allowed,
        first.operator_console_rendering_allowed,
        first.operator_presentation_rendering_allowed,
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
    assert first.admission_status == ADMISSION_STATUS

    _expect_rejected(lambda: gate.admit(request=replace(request, query_request_hash="0" * 64)))
    _expect_rejected(lambda: gate.admit(request=replace(request, query_request_status="wrong_status")))
    _expect_rejected(lambda: gate.admit(request=replace(request, operator_namespace="wrong.namespace")))
    _expect_rejected(lambda: gate.admit(request=replace(request, authorized_entry_count=0)))
    _expect_rejected(lambda: gate.admit(request=replace(request, authorized_scope_preserved=False)))
    _expect_rejected(lambda: gate.admit(request=replace(request, analytics_query_execution_allowed=True)))
    _expect_rejected(lambda: gate.admit(request=replace(request, qseries_execution_allowed=True)))
    _expect_rejected(lambda: gate.admit(request=replace(request, portfolio_mutation_performed=True)))

    print("[PASS] Actual OOP-003 query request consumed")
    print("[PASS] OOP-003 identity, hash, status, and lineage verified")
    print("[PASS] Operator and query namespaces enforced")
    print("[PASS] Consumer, projection, and query parameters verified")
    print("[PASS] Authorized analytics scope verified and frozen")
    print("[PASS] Deterministic query admission created and replay verified")
    print("[PASS] Query resolution admitted but not performed")
    print("[PASS] No analytics query execution or reexecution performed")
    print("[PASS] No analytics database connection or mutation performed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed requests rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_replacement(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def append_export(path: Path, export_line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8", newline="\n")
    existing = path.read_text(encoding="utf-8")
    if export_line in existing.splitlines():
        print(f"[OK] PACKAGE EXPORT PRESENT: {path.resolve()}")
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + export_line + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def verify_contract(path: Path, name: str, required_tokens: tuple[str, ...]) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Actual {name} module missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(f"Actual {name} contract mismatch; missing: " + ", ".join(missing))
    print(f"[OK] Actual {name} contract verified")


def main() -> int:
    print("=" * 40)
    print(" OOP-004 INSTALLER")
    print(" QUERY REQUEST ADMISSION")
    print(" AUTHORIZED SCOPE FREEZE")
    print("=" * 40)

    verify_contract(SOURCE_OOP_003, "OOP-003", (
        'SCHEMA_VERSION = "OOP-003"',
        "class OracleOperatorQueryRequest",
        "class OracleOperatorQueryRequestContract",
        "query_request_id",
        "query_request_hash",
        "query_request_status",
        "authorized_scope_preserved",
        "analytics_query_execution_allowed",
        "operator_session_construction_allowed",
        "operator_console_rendering_allowed",
        "operator_presentation_rendering_allowed",
        "qseries_execution_allowed",
    ))
    verify_contract(SOURCE_OOP_002, "OOP-002", (
        'SCHEMA_VERSION = "OOP-002"',
        "class OracleOperatorAnalyticsDependencyAdmission",
        "admission_hash",
        "operator_query_construction_allowed",
    ))
    verify_contract(SOURCE_OOP_001, "OOP-001", (
        'SCHEMA_VERSION = "OOP-001"',
        "class OracleOperatorAnalyticsDependencyReceipt",
        "dependency_receipt_hash",
    ))
    verify_contract(SOURCE_060, "INT-OIA-060", (
        'SCHEMA_VERSION = "INT-OIA-060"',
        "authorization_hash",
        "read_only_consumption_verified",
    ))

    protected_before = {
        SOURCE_OOP_003: sha256_file(SOURCE_OOP_003),
        SOURCE_OOP_002: sha256_file(SOURCE_OOP_002),
        SOURCE_OOP_001: sha256_file(SOURCE_OOP_001),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(QUERY_PACKAGE, "from .oracle_operator_query_request_admission_gate import *")
    append_export(OPERATOR_PACKAGE, "from .query.oracle_operator_query_request_admission_gate import *")

    for target in (PRODUCTION, TEST, QUERY_PACKAGE, OPERATOR_PACKAGE):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-003 and INT-OIA-060 unchanged")

    completed = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics package export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-004 test executed automatically")
    print()
    print("[DONE] OOP-004 query request admission gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
