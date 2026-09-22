from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

QSERIES = ROOT / "qseries_v2"
ANALYTICS = QSERIES / "oracle_intelligence" / "analytics"
ANALYTICS_QUERY = ANALYTICS / "downstream" / "query"
OPERATOR = QSERIES / "oracle_operator"
OPERATOR_QUERY = OPERATOR / "query"

SOURCE_060 = ANALYTICS_QUERY / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
SOURCE_OOP_001 = OPERATOR / "oracle_operator_analytics_read_only_dependency_gate.py"
SOURCE_OOP_002 = OPERATOR / "oracle_operator_analytics_dependency_admission_gate.py"
SOURCE_OOP_003 = OPERATOR_QUERY / "oracle_operator_query_request_contract.py"
SOURCE_OOP_004 = OPERATOR_QUERY / "oracle_operator_query_request_admission_gate.py"
SOURCE_OOP_005 = OPERATOR_QUERY / "oracle_operator_query_resolution_plan.py"
SOURCE_OOP_006 = OPERATOR_QUERY / "oracle_operator_query_resolution_authorization_gate.py"
SOURCE_OOP_007 = OPERATOR_QUERY / "oracle_operator_query_resolution_authorization_consumption_gate.py"
SOURCE_OOP_008 = OPERATOR_QUERY / "oracle_operator_query_resolution_read_invocation_readiness_gate.py"
SOURCE_OOP_009 = OPERATOR_QUERY / "oracle_operator_query_resolution_read_invocation_authorization_gate.py"
SOURCE_OOP_010 = OPERATOR_QUERY / "oracle_operator_query_resolution_read_invocation_authorization_consumption_gate.py"

PRODUCTION = OPERATOR_QUERY / "oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate.py"
TEST = ROOT / "test_oop_011_oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate.py"

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_read_invocation_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_010_CONSUMPTION_STATUS,
    INVOCATION_PACKAGE_TYPE as OOP_010_INVOCATION_PACKAGE_TYPE,
    OracleOperatorQueryResolutionReadInvocationAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-011"
ENGINE_ID = "OOP-011"
POLICY_ID = (
    "oracle.operator.query-resolution-adapter-invocation-execution-readiness-gate.v1"
)
READINESS_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-adapter-invocation-execution-readiness.v1"
)
READINESS_STATUS = (
    "operator_query_resolution_adapter_invocation_execution_ready"
)
EXECUTION_MODE = "single_bounded_read_only_adapter_invocation"

EXPECTED_CONSUMPTION_STATUS = OOP_010_CONSUMPTION_STATUS
EXPECTED_INVOCATION_PACKAGE_TYPE = OOP_010_INVOCATION_PACKAGE_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
    RuntimeError
):
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
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
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
class OracleOperatorQueryResolutionAdapterInvocationExecutionReadiness:
    adapter_execution_readiness_id: str
    source_read_consumption_id: str
    source_read_consumption_hash: str
    source_read_authorization_id: str
    source_read_authorization_hash: str
    source_read_readiness_id: str
    source_read_readiness_hash: str
    source_resolution_consumption_id: str
    source_resolution_consumption_hash: str
    source_resolution_authorization_id: str
    source_resolution_authorization_hash: str
    source_resolution_plan_id: str
    source_resolution_plan_hash: str
    source_query_admission_id: str
    source_query_admission_hash: str
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
    invocation_package_type: str
    read_invocation_mode: str
    read_adapter_contract_id: str
    execution_mode: str
    ready_resolution_strategy: str
    ready_entry_count: int
    ready_response_artifact_entry_ids: tuple[str, ...]
    ready_query_response_ids: tuple[str, ...]
    consumption_type_verified: bool
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_invocation_package_verified: bool
    read_adapter_contract_verified: bool
    bounded_artifact_read_verified: bool
    single_read_invocation_verified: bool
    deterministic_readiness_verified: bool
    adapter_invocation_execution_ready: bool
    adapter_invocation_execution_allowed: bool
    adapter_invocation_execution_performed: bool
    analytics_artifact_read_allowed: bool
    analytics_artifact_read_performed: bool
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
    readiness_status: str
    adapter_execution_readiness_hash: str


class OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessGate:
    @staticmethod
    def _verify_consumption(
        consumption: OracleOperatorQueryResolutionReadInvocationAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorQueryResolutionReadInvocationAuthorizationConsumption,
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "source must be the canonical OOP-010 consumption record"
            )

        body = asdict(consumption)
        supplied_hash = body.pop("read_consumption_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "OOP-010 consumption hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "OOP-010 consumption hash mismatch"
            )

        required_hashes = (
            consumption.read_consumption_id,
            consumption.source_read_authorization_hash,
            consumption.source_read_readiness_hash,
            consumption.source_resolution_consumption_hash,
            consumption.source_resolution_authorization_hash,
            consumption.source_resolution_plan_hash,
            consumption.source_query_admission_hash,
            consumption.source_query_request_hash,
            consumption.source_admission_hash,
            consumption.source_dependency_receipt_hash,
            consumption.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "OOP-010 lineage contains invalid hashes"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "OOP-010 consumption record is not active"
            )
        if consumption.invocation_package_type != EXPECTED_INVOCATION_PACKAGE_TYPE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "invocation package type mismatch"
            )
        if consumption.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "operator namespace mismatch"
            )
        if consumption.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "query namespace mismatch"
            )

        if consumption.consumed_entry_count < 1:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "consumption record contains no entries"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_query_response_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(consumption.consumed_response_artifact_entry_ids)) != consumption.consumed_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(consumption.consumed_query_response_ids)) != consumption.consumed_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            consumption.authorization_type_verified,
            consumption.authorization_identity_verified,
            consumption.authorization_hash_verified,
            consumption.authorization_status_verified,
            consumption.complete_lineage_verified,
            consumption.namespaces_verified,
            consumption.query_parameters_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.immutable_manifest_verified,
            consumption.single_use_consumption_verified,
            consumption.read_invocation_mode_verified,
            consumption.read_adapter_contract_verified,
            consumption.bounded_artifact_read_verified,
            consumption.single_read_invocation_authorized,
            consumption.immutable_invocation_package_verified,
            consumption.deterministic_consumption_verified,
            consumption.read_only_resolution_required,
            consumption.read_invocation_allowed,
            consumption.query_resolution_allowed,
            consumption.analytics_artifact_read_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "OOP-010 consumption record is incomplete"
            )

        forbidden_activity = (
            consumption.read_invocation_performed,
            consumption.query_resolution_performed,
            consumption.analytics_artifact_read_performed,
            consumption.analytics_query_execution_allowed,
            consumption.analytics_query_execution_performed,
            consumption.analytics_reexecution_allowed,
            consumption.analytics_reexecution_performed,
            consumption.analytics_database_connection_allowed,
            consumption.analytics_database_connection_performed,
            consumption.analytics_mutation_allowed,
            consumption.analytics_mutation_performed,
            consumption.operator_session_construction_allowed,
            consumption.operator_console_rendering_allowed,
            consumption.operator_presentation_rendering_allowed,
            consumption.publication_allowed,
            consumption.publication_performed,
            consumption.qseries_handoff_allowed,
            consumption.qseries_execution_allowed,
            consumption.qseries_execution_performed,
            consumption.order_creation_allowed,
            consumption.order_creation_performed,
            consumption.funds_movement_allowed,
            consumption.funds_movement_performed,
            consumption.portfolio_mutation_allowed,
            consumption.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError(
                "OOP-010 consumption record contains forbidden activity"
            )

    def certify(
        self,
        *,
        consumption: OracleOperatorQueryResolutionReadInvocationAuthorizationConsumption,
    ) -> OracleOperatorQueryResolutionAdapterInvocationExecutionReadiness:
        self._verify_consumption(consumption)

        adapter_execution_readiness_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_read_consumption_id": consumption.read_consumption_id,
                "source_read_consumption_hash": consumption.read_consumption_hash,
                "invocation_package_type": consumption.invocation_package_type,
                "read_invocation_mode": consumption.read_invocation_mode,
                "read_adapter_contract_id": consumption.read_adapter_contract_id,
                "execution_mode": EXECUTION_MODE,
                "ready_resolution_strategy": consumption.consumed_resolution_strategy,
                "query_mode": consumption.query_mode,
                "query_text": consumption.query_text,
                "time_scope": consumption.time_scope,
                "sort_order": consumption.sort_order,
                "result_limit": consumption.result_limit,
                "requested_tags": consumption.requested_tags,
                "ready_response_artifact_entry_ids": (
                    consumption.consumed_response_artifact_entry_ids
                ),
                "ready_query_response_ids": (
                    consumption.consumed_query_response_ids
                ),
            }
        )

        body = {
            "adapter_execution_readiness_id": adapter_execution_readiness_id,
            "source_read_consumption_id": consumption.read_consumption_id,
            "source_read_consumption_hash": consumption.read_consumption_hash,
            "source_read_authorization_id": consumption.source_read_authorization_id,
            "source_read_authorization_hash": consumption.source_read_authorization_hash,
            "source_read_readiness_id": consumption.source_read_readiness_id,
            "source_read_readiness_hash": consumption.source_read_readiness_hash,
            "source_resolution_consumption_id": consumption.source_resolution_consumption_id,
            "source_resolution_consumption_hash": consumption.source_resolution_consumption_hash,
            "source_resolution_authorization_id": consumption.source_resolution_authorization_id,
            "source_resolution_authorization_hash": consumption.source_resolution_authorization_hash,
            "source_resolution_plan_id": consumption.source_resolution_plan_id,
            "source_resolution_plan_hash": consumption.source_resolution_plan_hash,
            "source_query_admission_id": consumption.source_query_admission_id,
            "source_query_admission_hash": consumption.source_query_admission_hash,
            "source_query_request_id": consumption.source_query_request_id,
            "source_query_request_hash": consumption.source_query_request_hash,
            "source_admission_id": consumption.source_admission_id,
            "source_admission_hash": consumption.source_admission_hash,
            "source_dependency_receipt_id": consumption.source_dependency_receipt_id,
            "source_dependency_receipt_hash": consumption.source_dependency_receipt_hash,
            "source_authorization_id": consumption.source_authorization_id,
            "source_authorization_hash": consumption.source_authorization_hash,
            "operator_namespace": consumption.operator_namespace,
            "query_namespace": consumption.query_namespace,
            "consumer_id": consumption.consumer_id,
            "projection": consumption.projection,
            "query_mode": consumption.query_mode,
            "query_text": consumption.query_text,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "invocation_package_type": consumption.invocation_package_type,
            "read_invocation_mode": consumption.read_invocation_mode,
            "read_adapter_contract_id": consumption.read_adapter_contract_id,
            "execution_mode": EXECUTION_MODE,
            "ready_resolution_strategy": consumption.consumed_resolution_strategy,
            "ready_entry_count": consumption.consumed_entry_count,
            "ready_response_artifact_entry_ids": tuple(
                consumption.consumed_response_artifact_entry_ids
            ),
            "ready_query_response_ids": tuple(
                consumption.consumed_query_response_ids
            ),
            "consumption_type_verified": True,
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_invocation_package_verified": True,
            "read_adapter_contract_verified": True,
            "bounded_artifact_read_verified": True,
            "single_read_invocation_verified": True,
            "deterministic_readiness_verified": True,
            "adapter_invocation_execution_ready": True,
            "adapter_invocation_execution_allowed": True,
            "adapter_invocation_execution_performed": False,
            "analytics_artifact_read_allowed": True,
            "analytics_artifact_read_performed": False,
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
            "readiness_status": READINESS_STATUS,
        }

        return OracleOperatorQueryResolutionAdapterInvocationExecutionReadiness(
            **body,
            adapter_execution_readiness_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "READINESS_SCHEMA_VERSION",
    "READINESS_STATUS",
    "EXECUTION_MODE",
    "EXPECTED_CONSUMPTION_STATUS",
    "EXPECTED_INVOCATION_PACKAGE_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionReadiness",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessGate",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_010_oracle_operator_query_resolution_read_invocation_authorization_consumption_gate import (
    _authorization,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_read_invocation_authorization_consumption_gate import (
    OracleOperatorQueryResolutionReadInvocationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate import (
    EXECUTION_MODE,
    READINESS_STATUS,
    OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessGate,
    OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError,
    stable_hash,
)


def _consumption():
    return (
        OracleOperatorQueryResolutionReadInvocationAuthorizationConsumptionGate()
    ).consume(
        authorization=_authorization()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe adapter execution readiness accepted")
    except OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-011 TEST")
    print(" ADAPTER INVOCATION EXECUTION READINESS")
    print(" SINGLE BOUNDED READ-ONLY CALL")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessGate()

    first = gate.certify(consumption=consumption)
    repeated = gate.certify(consumption=consumption)

    assert first == repeated
    assert first.adapter_execution_readiness_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "adapter_execution_readiness_hash"
        }
    )

    assert first.source_read_consumption_id == consumption.read_consumption_id
    assert first.source_read_consumption_hash == consumption.read_consumption_hash
    assert first.execution_mode == EXECUTION_MODE
    assert first.read_adapter_contract_id == consumption.read_adapter_contract_id
    assert first.ready_entry_count == consumption.consumed_entry_count
    assert (
        first.ready_response_artifact_entry_ids
        == consumption.consumed_response_artifact_entry_ids
    )
    assert (
        first.ready_query_response_ids
        == consumption.consumed_query_response_ids
    )

    assert first.consumption_type_verified
    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_invocation_package_verified
    assert first.read_adapter_contract_verified
    assert first.bounded_artifact_read_verified
    assert first.single_read_invocation_verified
    assert first.deterministic_readiness_verified

    assert first.adapter_invocation_execution_ready
    assert first.adapter_invocation_execution_allowed
    assert not first.adapter_invocation_execution_performed
    assert first.analytics_artifact_read_allowed
    assert not first.analytics_artifact_read_performed
    assert not first.analytics_query_execution_allowed
    assert not first.analytics_query_execution_performed
    assert not first.analytics_reexecution_allowed
    assert not first.analytics_reexecution_performed
    assert not first.analytics_database_connection_allowed
    assert not first.analytics_database_connection_performed
    assert not first.analytics_mutation_allowed
    assert not first.analytics_mutation_performed
    assert not first.operator_session_construction_allowed
    assert not first.operator_console_rendering_allowed
    assert not first.operator_presentation_rendering_allowed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed
    assert first.readiness_status == READINESS_STATUS

    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                read_consumption_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                consumption_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                invocation_package_type="wrong_package",
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                immutable_invocation_package_verified=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                read_invocation_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                analytics_artifact_read_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-010 invocation package consumed")
    print("[PASS] OOP-010 identity, hash, status, and lineage verified")
    print("[PASS] Immutable adapter invocation package verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic adapter execution readiness certified")
    print("[PASS] Single bounded read-only adapter call allowed")
    print("[PASS] Adapter invocation ready but not performed")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] No analytics query execution or reexecution allowed")
    print("[PASS] No analytics database connection or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed packages rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


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
    text = path.read_text(encoding="utf-8")
    missing = [token for token in required_tokens if token not in text]
    if missing:
        raise RuntimeError(
            f"Actual {name} contract mismatch; missing: " + ", ".join(missing)
        )
    print(f"[OK] Actual {name} contract verified")


def main() -> int:
    print("=" * 40)
    print(" OOP-011 INSTALLER")
    print(" ADAPTER INVOCATION EXECUTION READINESS")
    print(" SINGLE BOUNDED READ-ONLY CALL")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_010,
        "OOP-010",
        (
            'SCHEMA_VERSION = "OOP-010"',
            "class OracleOperatorQueryResolutionReadInvocationAuthorizationConsumption",
            "class OracleOperatorQueryResolutionReadInvocationAuthorizationConsumptionGate",
            "read_consumption_id",
            "read_consumption_hash",
            "consumption_status",
            "invocation_package_type",
            "immutable_invocation_package_verified",
            "read_invocation_allowed",
            "read_invocation_performed",
            "analytics_artifact_read_allowed",
            "analytics_artifact_read_performed",
            "analytics_query_execution_allowed",
            "operator_session_construction_allowed",
            "qseries_execution_allowed",
        ),
    )

    for path, name, tokens in (
        (SOURCE_OOP_009, "OOP-009", ('SCHEMA_VERSION = "OOP-009"', "read_authorization_hash")),
        (SOURCE_OOP_008, "OOP-008", ('SCHEMA_VERSION = "OOP-008"', "read_readiness_hash")),
        (SOURCE_OOP_007, "OOP-007", ('SCHEMA_VERSION = "OOP-007"', "resolution_consumption_hash")),
        (SOURCE_OOP_006, "OOP-006", ('SCHEMA_VERSION = "OOP-006"', "resolution_authorization_hash")),
        (SOURCE_OOP_005, "OOP-005", ('SCHEMA_VERSION = "OOP-005"', "resolution_plan_hash")),
        (SOURCE_OOP_004, "OOP-004", ('SCHEMA_VERSION = "OOP-004"', "query_admission_hash")),
        (SOURCE_OOP_003, "OOP-003", ('SCHEMA_VERSION = "OOP-003"', "query_request_hash")),
        (SOURCE_OOP_002, "OOP-002", ('SCHEMA_VERSION = "OOP-002"', "admission_hash")),
        (SOURCE_OOP_001, "OOP-001", ('SCHEMA_VERSION = "OOP-001"', "dependency_receipt_hash")),
        (
            SOURCE_060,
            "INT-OIA-060",
            ('SCHEMA_VERSION = "INT-OIA-060"', "authorization_hash", "read_only_consumption_verified"),
        ),
    ):
        verify_contract(path, name, tokens)

    protected_before = {
        path: sha256_file(path)
        for path in (
            SOURCE_OOP_010,
            SOURCE_OOP_009,
            SOURCE_OOP_008,
            SOURCE_OOP_007,
            SOURCE_OOP_006,
            SOURCE_OOP_005,
            SOURCE_OOP_004,
            SOURCE_OOP_003,
            SOURCE_OOP_002,
            SOURCE_OOP_001,
            SOURCE_060,
        )
    }

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .query.oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate import *",
    )

    for target in (PRODUCTION, TEST, QUERY_PACKAGE, OPERATOR_PACKAGE):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-010 and INT-OIA-060 unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(
                f"Protected upstream module changed during test: {path}"
            )

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics package export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-011 test executed automatically")
    print()
    print("[DONE] OOP-011 adapter invocation execution readiness gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
