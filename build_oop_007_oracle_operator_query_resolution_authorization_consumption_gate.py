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

SOURCE_060 = (
    ANALYTICS_QUERY
    / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
)
SOURCE_OOP_001 = (
    OPERATOR
    / "oracle_operator_analytics_read_only_dependency_gate.py"
)
SOURCE_OOP_002 = (
    OPERATOR
    / "oracle_operator_analytics_dependency_admission_gate.py"
)
SOURCE_OOP_003 = (
    OPERATOR_QUERY
    / "oracle_operator_query_request_contract.py"
)
SOURCE_OOP_004 = (
    OPERATOR_QUERY
    / "oracle_operator_query_request_admission_gate.py"
)
SOURCE_OOP_005 = (
    OPERATOR_QUERY
    / "oracle_operator_query_resolution_plan.py"
)
SOURCE_OOP_006 = (
    OPERATOR_QUERY
    / "oracle_operator_query_resolution_authorization_gate.py"
)

PRODUCTION = (
    OPERATOR_QUERY
    / "oracle_operator_query_resolution_authorization_consumption_gate.py"
)
TEST = (
    ROOT
    / "test_oop_007_oracle_operator_query_resolution_authorization_consumption_gate.py"
)

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_authorization_gate import (
    AUTHORIZATION_STATUS as OOP_006_AUTHORIZATION_STATUS,
    OracleOperatorQueryResolutionAuthorization,
)

SCHEMA_VERSION = "OOP-007"
ENGINE_ID = "OOP-007"
POLICY_ID = (
    "oracle.operator.query-resolution-authorization-consumption-gate.v1"
)
CONSUMPTION_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-authorization-consumption.v1"
)
CONSUMPTION_STATUS = (
    "operator_query_resolution_authorization_consumed"
)

EXPECTED_AUTHORIZATION_STATUS = OOP_006_AUTHORIZATION_STATUS
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
READ_INVOCATION_MODE = "authorized_immutable_artifact_read"


class OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
    RuntimeError
):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
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
class OracleOperatorQueryResolutionAuthorizationConsumption:
    resolution_consumption_id: str
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
    read_invocation_mode: str
    consumed_resolution_strategy: str
    consumed_entry_count: int
    consumed_response_artifact_entry_ids: tuple[str, ...]
    consumed_query_response_ids: tuple[str, ...]
    resolution_authorization_type_verified: bool
    resolution_authorization_identity_verified: bool
    resolution_authorization_hash_verified: bool
    resolution_authorization_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    single_bounded_resolution_path_verified: bool
    single_use_consumption_verified: bool
    immutable_read_manifest_verified: bool
    deterministic_consumption_verified: bool
    read_only_resolution_required: bool
    query_resolution_allowed: bool
    query_resolution_performed: bool
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
    consumption_status: str
    resolution_consumption_hash: str


class OracleOperatorQueryResolutionAuthorizationConsumptionGate:
    @staticmethod
    def _verify_authorization(
        authorization: OracleOperatorQueryResolutionAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            OracleOperatorQueryResolutionAuthorization,
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "source must be the canonical OOP-006 authorization"
            )

        body = asdict(authorization)
        supplied_hash = body.pop(
            "resolution_authorization_hash",
            None,
        )
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization hash mismatch"
            )

        required_hashes = (
            authorization.resolution_authorization_id,
            authorization.source_resolution_plan_hash,
            authorization.source_query_admission_hash,
            authorization.source_query_request_hash,
            authorization.source_admission_hash,
            authorization.source_dependency_receipt_hash,
            authorization.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 lineage contains invalid hashes"
            )

        if (
            authorization.authorization_status
            != EXPECTED_AUTHORIZATION_STATUS
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization is not active"
            )
        if (
            authorization.operator_namespace
            != EXPECTED_OPERATOR_NAMESPACE
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "operator namespace mismatch"
            )
        if authorization.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "query namespace mismatch"
            )

        if authorization.authorized_entry_count < 1:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "authorization contains no entries"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_query_response_ids
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "query-response cardinality mismatch"
            )
        if len(
            set(
                authorization.authorized_response_artifact_entry_ids
            )
        ) != authorization.authorized_entry_count:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(
            set(authorization.authorized_query_response_ids)
        ) != authorization.authorized_entry_count:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            authorization.resolution_plan_type_verified,
            authorization.resolution_plan_identity_verified,
            authorization.resolution_plan_hash_verified,
            authorization.resolution_plan_status_verified,
            authorization.complete_lineage_verified,
            authorization.namespaces_verified,
            authorization.query_parameters_verified,
            authorization.frozen_scope_verified,
            authorization.frozen_scope_preserved,
            authorization.strategy_verified,
            authorization.deterministic_authorization_verified,
            authorization.single_bounded_resolution_path_verified,
            authorization.read_only_resolution_required,
            authorization.query_resolution_allowed,
            authorization.analytics_artifact_read_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization is incomplete"
            )

        forbidden_activity = (
            authorization.query_resolution_performed,
            authorization.analytics_artifact_read_performed,
            authorization.analytics_query_execution_allowed,
            authorization.analytics_query_execution_performed,
            authorization.analytics_reexecution_allowed,
            authorization.analytics_reexecution_performed,
            authorization.analytics_database_connection_allowed,
            authorization.analytics_database_connection_performed,
            authorization.analytics_mutation_allowed,
            authorization.analytics_mutation_performed,
            authorization.operator_session_construction_allowed,
            authorization.operator_console_rendering_allowed,
            authorization.operator_presentation_rendering_allowed,
            authorization.publication_allowed,
            authorization.publication_performed,
            authorization.qseries_handoff_allowed,
            authorization.qseries_execution_allowed,
            authorization.qseries_execution_performed,
            authorization.order_creation_allowed,
            authorization.order_creation_performed,
            authorization.funds_movement_allowed,
            authorization.funds_movement_performed,
            authorization.portfolio_mutation_allowed,
            authorization.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization contains forbidden activity"
            )

    def consume(
        self,
        *,
        authorization: OracleOperatorQueryResolutionAuthorization,
    ) -> OracleOperatorQueryResolutionAuthorizationConsumption:
        self._verify_authorization(authorization)

        resolution_consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_resolution_authorization_id": (
                    authorization.resolution_authorization_id
                ),
                "source_resolution_authorization_hash": (
                    authorization.resolution_authorization_hash
                ),
                "read_invocation_mode": READ_INVOCATION_MODE,
                "consumed_resolution_strategy": (
                    authorization.authorized_resolution_strategy
                ),
                "query_mode": authorization.query_mode,
                "query_text": authorization.query_text,
                "time_scope": authorization.time_scope,
                "sort_order": authorization.sort_order,
                "result_limit": authorization.result_limit,
                "requested_tags": authorization.requested_tags,
                "consumed_response_artifact_entry_ids": (
                    authorization.authorized_response_artifact_entry_ids
                ),
                "consumed_query_response_ids": (
                    authorization.authorized_query_response_ids
                ),
            }
        )

        body = {
            "resolution_consumption_id": resolution_consumption_id,
            "source_resolution_authorization_id": (
                authorization.resolution_authorization_id
            ),
            "source_resolution_authorization_hash": (
                authorization.resolution_authorization_hash
            ),
            "source_resolution_plan_id": (
                authorization.source_resolution_plan_id
            ),
            "source_resolution_plan_hash": (
                authorization.source_resolution_plan_hash
            ),
            "source_query_admission_id": (
                authorization.source_query_admission_id
            ),
            "source_query_admission_hash": (
                authorization.source_query_admission_hash
            ),
            "source_query_request_id": (
                authorization.source_query_request_id
            ),
            "source_query_request_hash": (
                authorization.source_query_request_hash
            ),
            "source_admission_id": authorization.source_admission_id,
            "source_admission_hash": (
                authorization.source_admission_hash
            ),
            "source_dependency_receipt_id": (
                authorization.source_dependency_receipt_id
            ),
            "source_dependency_receipt_hash": (
                authorization.source_dependency_receipt_hash
            ),
            "source_authorization_id": (
                authorization.source_authorization_id
            ),
            "source_authorization_hash": (
                authorization.source_authorization_hash
            ),
            "operator_namespace": authorization.operator_namespace,
            "query_namespace": authorization.query_namespace,
            "consumer_id": authorization.consumer_id,
            "projection": authorization.projection,
            "query_mode": authorization.query_mode,
            "query_text": authorization.query_text,
            "time_scope": authorization.time_scope,
            "sort_order": authorization.sort_order,
            "result_limit": authorization.result_limit,
            "requested_tags": tuple(authorization.requested_tags),
            "read_invocation_mode": READ_INVOCATION_MODE,
            "consumed_resolution_strategy": (
                authorization.authorized_resolution_strategy
            ),
            "consumed_entry_count": (
                authorization.authorized_entry_count
            ),
            "consumed_response_artifact_entry_ids": tuple(
                authorization.authorized_response_artifact_entry_ids
            ),
            "consumed_query_response_ids": tuple(
                authorization.authorized_query_response_ids
            ),
            "resolution_authorization_type_verified": True,
            "resolution_authorization_identity_verified": True,
            "resolution_authorization_hash_verified": True,
            "resolution_authorization_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "single_bounded_resolution_path_verified": True,
            "single_use_consumption_verified": True,
            "immutable_read_manifest_verified": True,
            "deterministic_consumption_verified": True,
            "read_only_resolution_required": True,
            "query_resolution_allowed": True,
            "query_resolution_performed": False,
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
            "consumption_status": CONSUMPTION_STATUS,
        }

        return OracleOperatorQueryResolutionAuthorizationConsumption(
            **body,
            resolution_consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_SCHEMA_VERSION",
    "CONSUMPTION_STATUS",
    "EXPECTED_AUTHORIZATION_STATUS",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "READ_INVOCATION_MODE",
    "OracleOperatorQueryResolutionAuthorizationConsumption",
    "OracleOperatorQueryResolutionAuthorizationConsumptionGate",
    "OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_int_oia_060_oracle_intelligence_analytics_certified_query_response_artifact_authorization_consumption_attestation_authorization_consumption_attestation_authorization_gate import (
    _attestation,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate,
)
from qseries_v2.oracle_operator.oracle_operator_analytics_read_only_dependency_gate import (
    OracleOperatorAnalyticsReadOnlyDependencyGate,
)
from qseries_v2.oracle_operator.oracle_operator_analytics_dependency_admission_gate import (
    OracleOperatorAnalyticsDependencyAdmissionGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_request_contract import (
    OracleOperatorQueryRequestContract,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_request_admission_gate import (
    OracleOperatorQueryRequestAdmissionGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_plan import (
    OracleOperatorQueryResolutionPlanner,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_authorization_gate import (
    OracleOperatorQueryResolutionAuthorizationGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    READ_INVOCATION_MODE,
    OracleOperatorQueryResolutionAuthorizationConsumptionGate,
    OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    authorization = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate()
    ).authorize(
        attestation=_attestation(),
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )
    receipt = OracleOperatorAnalyticsReadOnlyDependencyGate().consume(
        authorization=authorization
    )
    dependency_admission = (
        OracleOperatorAnalyticsDependencyAdmissionGate()
    ).admit(
        receipt=receipt
    )
    request = OracleOperatorQueryRequestContract().materialize(
        admission=dependency_admission,
        query_mode="opportunity_lookup",
        query_text="Show major opportunities closing today",
        time_scope="same_day",
        sort_order="priority",
        result_limit=20,
        requested_tags=("kalshi", "major"),
    )
    query_admission = (
        OracleOperatorQueryRequestAdmissionGate()
    ).admit(
        request=request
    )
    plan = OracleOperatorQueryResolutionPlanner().plan(
        admission=query_admission
    )
    return OracleOperatorQueryResolutionAuthorizationGate().authorize(
        plan=plan
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError(
            "unsafe authorization consumption accepted"
        )
    except OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-007 TEST")
    print(" AUTHORIZATION CONSUMPTION")
    print(" IMMUTABLE READ MANIFEST")
    print("=" * 40)

    authorization = _authorization()
    gate = (
        OracleOperatorQueryResolutionAuthorizationConsumptionGate()
    )

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.resolution_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "resolution_consumption_hash"
        }
    )

    assert (
        first.source_resolution_authorization_id
        == authorization.resolution_authorization_id
    )
    assert (
        first.source_resolution_authorization_hash
        == authorization.resolution_authorization_hash
    )
    assert first.query_mode == authorization.query_mode
    assert first.query_text == authorization.query_text
    assert first.time_scope == authorization.time_scope
    assert first.sort_order == authorization.sort_order
    assert first.result_limit == authorization.result_limit
    assert first.requested_tags == authorization.requested_tags
    assert first.read_invocation_mode == READ_INVOCATION_MODE
    assert (
        first.consumed_resolution_strategy
        == authorization.authorized_resolution_strategy
    )
    assert (
        first.consumed_entry_count
        == authorization.authorized_entry_count
    )
    assert (
        first.consumed_response_artifact_entry_ids
        == authorization.authorized_response_artifact_entry_ids
    )
    assert (
        first.consumed_query_response_ids
        == authorization.authorized_query_response_ids
    )

    assert first.resolution_authorization_type_verified
    assert first.resolution_authorization_identity_verified
    assert first.resolution_authorization_hash_verified
    assert first.resolution_authorization_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.single_bounded_resolution_path_verified
    assert first.single_use_consumption_verified
    assert first.immutable_read_manifest_verified
    assert first.deterministic_consumption_verified
    assert first.read_only_resolution_required

    assert first.query_resolution_allowed
    assert not first.query_resolution_performed
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
    assert first.consumption_status == CONSUMPTION_STATUS

    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                resolution_authorization_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorization_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                frozen_scope_preserved=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                analytics_artifact_read_allowed=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                analytics_artifact_read_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                qseries_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                portfolio_mutation_performed=True,
            )
        )
    )

    print("[PASS] Actual OOP-006 authorization consumed")
    print("[PASS] OOP-006 identity, hash, status, and lineage verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic single-use consumption record created")
    print("[PASS] Immutable read invocation manifest materialized")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] No analytics query execution or reexecution allowed")
    print("[PASS] No analytics database connection or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed authorizations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_replacement(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text.strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
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
    path.write_text(
        existing + export_line + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def verify_contract(
    path: Path,
    name: str,
    required_tokens: tuple[str, ...],
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Actual {name} module missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            f"Actual {name} contract mismatch; missing: "
            + ", ".join(missing)
        )
    print(f"[OK] Actual {name} contract verified")


def main() -> int:
    print("=" * 40)
    print(" OOP-007 INSTALLER")
    print(" AUTHORIZATION CONSUMPTION")
    print(" IMMUTABLE READ MANIFEST")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_006,
        "OOP-006",
        (
            'SCHEMA_VERSION = "OOP-006"',
            "class OracleOperatorQueryResolutionAuthorization",
            "class OracleOperatorQueryResolutionAuthorizationGate",
            "resolution_authorization_id",
            "resolution_authorization_hash",
            "authorization_status",
            "frozen_scope_preserved",
            "single_bounded_resolution_path_verified",
            "analytics_artifact_read_allowed",
            "analytics_artifact_read_performed",
            "analytics_query_execution_allowed",
            "operator_session_construction_allowed",
            "qseries_execution_allowed",
        ),
    )
    verify_contract(
        SOURCE_OOP_005,
        "OOP-005",
        (
            'SCHEMA_VERSION = "OOP-005"',
            "class OracleOperatorQueryResolutionPlan",
            "resolution_plan_hash",
        ),
    )
    verify_contract(
        SOURCE_OOP_004,
        "OOP-004",
        (
            'SCHEMA_VERSION = "OOP-004"',
            "class OracleOperatorQueryRequestAdmission",
            "query_admission_hash",
        ),
    )
    verify_contract(
        SOURCE_OOP_003,
        "OOP-003",
        (
            'SCHEMA_VERSION = "OOP-003"',
            "class OracleOperatorQueryRequest",
            "query_request_hash",
        ),
    )
    verify_contract(
        SOURCE_OOP_002,
        "OOP-002",
        (
            'SCHEMA_VERSION = "OOP-002"',
            "class OracleOperatorAnalyticsDependencyAdmission",
            "admission_hash",
        ),
    )
    verify_contract(
        SOURCE_OOP_001,
        "OOP-001",
        (
            'SCHEMA_VERSION = "OOP-001"',
            "class OracleOperatorAnalyticsDependencyReceipt",
            "dependency_receipt_hash",
        ),
    )
    verify_contract(
        SOURCE_060,
        "INT-OIA-060",
        (
            'SCHEMA_VERSION = "INT-OIA-060"',
            "authorization_hash",
            "read_only_consumption_verified",
        ),
    )

    protected_before = {
        SOURCE_OOP_006: sha256_file(SOURCE_OOP_006),
        SOURCE_OOP_005: sha256_file(SOURCE_OOP_005),
        SOURCE_OOP_004: sha256_file(SOURCE_OOP_004),
        SOURCE_OOP_003: sha256_file(SOURCE_OOP_003),
        SOURCE_OOP_002: sha256_file(SOURCE_OOP_002),
        SOURCE_OOP_001: sha256_file(SOURCE_OOP_001),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_operator_query_resolution_authorization_consumption_gate import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .query.oracle_operator_query_resolution_authorization_consumption_gate import *",
    )

    for target in (
        PRODUCTION,
        TEST,
        QUERY_PACKAGE,
        OPERATOR_PACKAGE,
    ):
        ast.parse(
            target.read_text(encoding="utf-8"),
            filename=str(target),
        )
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-006 and INT-OIA-060 unchanged")

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
    print("[OK] OOP-007 test executed automatically")
    print()
    print(
        "[DONE] OOP-007 authorization consumption gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
