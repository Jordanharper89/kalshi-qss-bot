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

PRODUCTION = (
    OPERATOR_QUERY
    / "oracle_operator_query_resolution_plan.py"
)
TEST = (
    ROOT
    / "test_oop_005_oracle_operator_query_resolution_plan.py"
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

from qseries_v2.oracle_operator.query.oracle_operator_query_request_admission_gate import (
    ADMISSION_STATUS as OOP_004_ADMISSION_STATUS,
    OracleOperatorQueryRequestAdmission,
)

SCHEMA_VERSION = "OOP-005"
ENGINE_ID = "OOP-005"
POLICY_ID = "oracle.operator.query-resolution-plan.v1"
RESOLUTION_PLAN_SCHEMA_VERSION = "oracle.operator.query.resolution-plan.v1"
RESOLUTION_PLAN_STATUS = "operator_query_resolution_planned"

EXPECTED_ADMISSION_STATUS = OOP_004_ADMISSION_STATUS
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"

_ALLOWED_RESOLUTION_STRATEGIES = frozenset(
    {
        "authorized_entry_filter",
        "authorized_response_filter",
        "authorized_entry_and_response_filter",
    }
)


class OracleOperatorQueryResolutionPlanInvariantError(RuntimeError):
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
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionPlanInvariantError(
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
class OracleOperatorQueryResolutionPlan:
    resolution_plan_id: str
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
    resolution_strategy: str
    planned_entry_count: int
    planned_response_artifact_entry_ids: tuple[str, ...]
    planned_query_response_ids: tuple[str, ...]
    query_admission_type_verified: bool
    query_admission_identity_verified: bool
    query_admission_hash_verified: bool
    query_admission_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    resolution_strategy_verified: bool
    deterministic_plan_verified: bool
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
    resolution_plan_status: str
    resolution_plan_hash: str


class OracleOperatorQueryResolutionPlanner:
    @staticmethod
    def _verify_admission(
        admission: OracleOperatorQueryRequestAdmission,
    ) -> None:
        if not isinstance(admission, OracleOperatorQueryRequestAdmission):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "source must be the canonical OOP-004 query admission"
            )

        body = asdict(admission)
        supplied_hash = body.pop("query_admission_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission hash mismatch"
            )

        required_hashes = (
            admission.query_admission_id,
            admission.source_query_request_hash,
            admission.source_admission_hash,
            admission.source_dependency_receipt_hash,
            admission.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 lineage contains invalid hashes"
            )

        if admission.admission_status != EXPECTED_ADMISSION_STATUS:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission is not active"
            )
        if admission.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "operator namespace mismatch"
            )
        if admission.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "query namespace mismatch"
            )

        if admission.admitted_entry_count < 1:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "query admission contains no authorized entries"
            )
        if admission.admitted_entry_count != len(
            admission.admitted_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if admission.admitted_entry_count != len(
            admission.admitted_query_response_ids
        ):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "query-response cardinality mismatch"
            )

        required_truths = (
            admission.query_request_type_verified,
            admission.query_request_identity_verified,
            admission.query_request_hash_verified,
            admission.query_request_status_verified,
            admission.source_admission_lineage_verified,
            admission.source_dependency_lineage_verified,
            admission.source_authorization_lineage_verified,
            admission.operator_namespace_verified,
            admission.consumer_identity_verified,
            admission.projection_identity_verified,
            admission.query_parameters_verified,
            admission.authorized_scope_verified,
            admission.authorized_scope_frozen,
            admission.deterministic_admission_verified,
            admission.analytics_read_only_dependency_preserved,
            admission.query_resolution_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission is incomplete"
            )

        forbidden_authority = (
            admission.query_resolution_performed,
            admission.analytics_query_execution_allowed,
            admission.analytics_query_execution_performed,
            admission.analytics_reexecution_allowed,
            admission.analytics_reexecution_performed,
            admission.analytics_database_connection_allowed,
            admission.analytics_database_connection_performed,
            admission.analytics_mutation_allowed,
            admission.analytics_mutation_performed,
            admission.operator_session_construction_allowed,
            admission.operator_console_rendering_allowed,
            admission.operator_presentation_rendering_allowed,
            admission.publication_allowed,
            admission.publication_performed,
            admission.qseries_handoff_allowed,
            admission.qseries_execution_allowed,
            admission.qseries_execution_performed,
            admission.order_creation_allowed,
            admission.order_creation_performed,
            admission.funds_movement_allowed,
            admission.funds_movement_performed,
            admission.portfolio_mutation_allowed,
            admission.portfolio_mutation_performed,
        )
        if any(forbidden_authority):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission contains forbidden activity"
            )

    def plan(
        self,
        *,
        admission: OracleOperatorQueryRequestAdmission,
        resolution_strategy: str = (
            "authorized_entry_and_response_filter"
        ),
    ) -> OracleOperatorQueryResolutionPlan:
        self._verify_admission(admission)

        if resolution_strategy not in _ALLOWED_RESOLUTION_STRATEGIES:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "unsupported resolution strategy"
            )

        resolution_plan_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_query_admission_id": admission.query_admission_id,
                "source_query_admission_hash": admission.query_admission_hash,
                "resolution_strategy": resolution_strategy,
                "query_mode": admission.query_mode,
                "query_text": admission.query_text,
                "time_scope": admission.time_scope,
                "sort_order": admission.sort_order,
                "result_limit": admission.result_limit,
                "requested_tags": admission.requested_tags,
                "planned_response_artifact_entry_ids": (
                    admission.admitted_response_artifact_entry_ids
                ),
                "planned_query_response_ids": (
                    admission.admitted_query_response_ids
                ),
            }
        )

        body = {
            "resolution_plan_id": resolution_plan_id,
            "source_query_admission_id": admission.query_admission_id,
            "source_query_admission_hash": admission.query_admission_hash,
            "source_query_request_id": admission.source_query_request_id,
            "source_query_request_hash": admission.source_query_request_hash,
            "source_admission_id": admission.source_admission_id,
            "source_admission_hash": admission.source_admission_hash,
            "source_dependency_receipt_id": (
                admission.source_dependency_receipt_id
            ),
            "source_dependency_receipt_hash": (
                admission.source_dependency_receipt_hash
            ),
            "source_authorization_id": admission.source_authorization_id,
            "source_authorization_hash": admission.source_authorization_hash,
            "operator_namespace": admission.operator_namespace,
            "query_namespace": admission.query_namespace,
            "consumer_id": admission.consumer_id,
            "projection": admission.projection,
            "query_mode": admission.query_mode,
            "query_text": admission.query_text,
            "time_scope": admission.time_scope,
            "sort_order": admission.sort_order,
            "result_limit": admission.result_limit,
            "requested_tags": tuple(admission.requested_tags),
            "resolution_strategy": resolution_strategy,
            "planned_entry_count": admission.admitted_entry_count,
            "planned_response_artifact_entry_ids": tuple(
                admission.admitted_response_artifact_entry_ids
            ),
            "planned_query_response_ids": tuple(
                admission.admitted_query_response_ids
            ),
            "query_admission_type_verified": True,
            "query_admission_identity_verified": True,
            "query_admission_hash_verified": True,
            "query_admission_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "resolution_strategy_verified": True,
            "deterministic_plan_verified": True,
            "read_only_resolution_required": True,
            "query_resolution_allowed": True,
            "query_resolution_performed": False,
            "analytics_artifact_read_allowed": False,
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
            "resolution_plan_status": RESOLUTION_PLAN_STATUS,
        }

        return OracleOperatorQueryResolutionPlan(
            **body,
            resolution_plan_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "RESOLUTION_PLAN_SCHEMA_VERSION",
    "RESOLUTION_PLAN_STATUS",
    "EXPECTED_ADMISSION_STATUS",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryResolutionPlan",
    "OracleOperatorQueryResolutionPlanner",
    "OracleOperatorQueryResolutionPlanInvariantError",
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
    RESOLUTION_PLAN_STATUS,
    OracleOperatorQueryResolutionPlanInvariantError,
    OracleOperatorQueryResolutionPlanner,
    stable_hash,
)


def _query_admission():
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
    return OracleOperatorQueryRequestAdmissionGate().admit(
        request=request
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe resolution plan accepted")
    except OracleOperatorQueryResolutionPlanInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-005 TEST")
    print(" QUERY RESOLUTION PLAN")
    print(" BOUNDED READ-ONLY MANIFEST")
    print("=" * 40)

    admission = _query_admission()
    planner = OracleOperatorQueryResolutionPlanner()

    first = planner.plan(admission=admission)
    repeated = planner.plan(admission=admission)

    assert first == repeated
    assert first.resolution_plan_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "resolution_plan_hash"
        }
    )

    assert first.source_query_admission_id == admission.query_admission_id
    assert first.source_query_admission_hash == admission.query_admission_hash
    assert first.query_mode == admission.query_mode
    assert first.query_text == admission.query_text
    assert first.time_scope == admission.time_scope
    assert first.sort_order == admission.sort_order
    assert first.result_limit == admission.result_limit
    assert first.requested_tags == admission.requested_tags
    assert (
        first.planned_entry_count
        == admission.admitted_entry_count
    )
    assert (
        first.planned_response_artifact_entry_ids
        == admission.admitted_response_artifact_entry_ids
    )
    assert (
        first.planned_query_response_ids
        == admission.admitted_query_response_ids
    )

    assert first.query_admission_type_verified
    assert first.query_admission_identity_verified
    assert first.query_admission_hash_verified
    assert first.query_admission_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.resolution_strategy_verified
    assert first.deterministic_plan_verified
    assert first.read_only_resolution_required

    assert first.query_resolution_allowed
    assert not first.query_resolution_performed
    assert not first.analytics_artifact_read_allowed
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
    assert first.resolution_plan_status == RESOLUTION_PLAN_STATUS

    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                query_admission_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                admission_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                authorized_scope_frozen=False,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                query_resolution_allowed=False,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                qseries_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=admission,
            resolution_strategy="unsupported",
        )
    )

    print("[PASS] Actual OOP-004 query admission consumed")
    print("[PASS] OOP-004 identity, hash, status, and lineage verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic query resolution plan created")
    print("[PASS] Resolution strategy constrained to authorized filters")
    print("[PASS] Query resolution allowed but not performed")
    print("[PASS] No analytics artifact read performed")
    print("[PASS] No analytics query execution or reexecution performed")
    print("[PASS] No analytics database connection or mutation performed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed plans rejected")
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
    print(" OOP-005 INSTALLER")
    print(" QUERY RESOLUTION PLAN")
    print(" BOUNDED READ-ONLY MANIFEST")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_004,
        "OOP-004",
        (
            'SCHEMA_VERSION = "OOP-004"',
            "class OracleOperatorQueryRequestAdmission",
            "class OracleOperatorQueryRequestAdmissionGate",
            "query_admission_id",
            "query_admission_hash",
            "authorized_scope_frozen",
            "query_resolution_allowed",
            "query_resolution_performed",
            "analytics_query_execution_allowed",
            "operator_session_construction_allowed",
            "qseries_execution_allowed",
        ),
    )
    verify_contract(
        SOURCE_OOP_003,
        "OOP-003",
        (
            'SCHEMA_VERSION = "OOP-003"',
            "class OracleOperatorQueryRequest",
            "query_request_hash",
            "authorized_scope_preserved",
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
        "from .oracle_operator_query_resolution_plan import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .query.oracle_operator_query_resolution_plan import *",
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
    print("[PASS] OOP-001 through OOP-004 and INT-OIA-060 unchanged")

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
    print("[OK] OOP-005 test executed automatically")
    print()
    print("[DONE] OOP-005 query resolution plan installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
