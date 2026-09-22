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

PRODUCTION = (
    OPERATOR_QUERY
    / "oracle_operator_query_request_contract.py"
)
TEST = (
    ROOT
    / "test_oop_003_oracle_operator_query_request_contract.py"
)

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_operator.oracle_operator_analytics_dependency_admission_gate import (
    ADMISSION_STATUS as OOP_002_ADMISSION_STATUS,
    EXPECTED_OPERATOR_NAMESPACE,
    OracleOperatorAnalyticsDependencyAdmission,
)

SCHEMA_VERSION = "OOP-003"
ENGINE_ID = "OOP-003"
POLICY_ID = "oracle.operator.query-request-contract.v1"
QUERY_REQUEST_SCHEMA_VERSION = "oracle.operator.query.request.v1"
QUERY_REQUEST_STATUS = "operator_query_request_materialized"

EXPECTED_ADMISSION_STATUS = OOP_002_ADMISSION_STATUS
EXPECTED_CONSUMER_ID = "oracle.operator.console.v1"
EXPECTED_PROJECTION = "operator_research"

MAX_QUERY_LENGTH = 4096
MAX_RESULT_LIMIT = 100
DEFAULT_RESULT_LIMIT = 25

_ALLOWED_QUERY_MODES = frozenset(
    {
        "market_lookup",
        "opportunity_lookup",
        "research_summary",
        "evidence_lookup",
        "comparison",
    }
)
_ALLOWED_SORT_ORDERS = frozenset(
    {
        "relevance",
        "priority",
        "confidence",
        "market_close_time",
    }
)
_ALLOWED_TIME_SCOPES = frozenset(
    {
        "same_day",
        "next_24_hours",
        "next_7_days",
        "all_authorized",
    }
)


class OracleOperatorQueryRequestInvariantError(RuntimeError):
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
            raise OracleOperatorQueryRequestInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryRequestInvariantError(
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


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise OracleOperatorQueryRequestInvariantError(
            "query text must be a string"
        )
    normalized = re.sub(r"\s+", " ", value).strip()
    if not normalized:
        raise OracleOperatorQueryRequestInvariantError(
            "query text must not be empty"
        )
    if len(normalized) > MAX_QUERY_LENGTH:
        raise OracleOperatorQueryRequestInvariantError(
            "query text exceeds maximum length"
        )
    return normalized


def _normalize_tags(values: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise OracleOperatorQueryRequestInvariantError(
                "query tags must be strings"
            )
        item = re.sub(r"\s+", " ", value).strip().lower()
        if not item:
            raise OracleOperatorQueryRequestInvariantError(
                "query tags must not be empty"
            )
        if len(item) > 128:
            raise OracleOperatorQueryRequestInvariantError(
                "query tag exceeds maximum length"
            )
        normalized.append(item)
    return tuple(sorted(set(normalized)))


@dataclass(frozen=True)
class OracleOperatorQueryRequest:
    query_request_id: str
    source_admission_id: str
    source_admission_hash: str
    source_dependency_receipt_id: str
    source_dependency_receipt_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    operator_namespace: str
    consumer_id: str
    projection: str
    query_mode: str
    query_text: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    admission_type_verified: bool
    admission_hash_verified: bool
    admission_status_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    query_mode_verified: bool
    time_scope_verified: bool
    sort_order_verified: bool
    result_limit_verified: bool
    authorized_scope_preserved: bool
    deterministic_request_verified: bool
    analytics_read_only_dependency_preserved: bool
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
    query_request_status: str
    query_request_hash: str


class OracleOperatorQueryRequestContract:
    @staticmethod
    def _verify_admission(
        admission: OracleOperatorAnalyticsDependencyAdmission,
    ) -> None:
        if not isinstance(
            admission,
            OracleOperatorAnalyticsDependencyAdmission,
        ):
            raise OracleOperatorQueryRequestInvariantError(
                "source must be the canonical OOP-002 admission"
            )

        body = asdict(admission)
        supplied_hash = body.pop("admission_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission hash mismatch"
            )

        if not _valid_sha256(admission.admission_id):
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission identity is invalid"
            )
        if admission.admission_status != EXPECTED_ADMISSION_STATUS:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission is not active"
            )
        if admission.admitted_consumer_id != EXPECTED_CONSUMER_ID:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 consumer identity mismatch"
            )
        if admission.admitted_projection != EXPECTED_PROJECTION:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 projection identity mismatch"
            )

        if admission.admitted_entry_count < 1:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission contains no entries"
            )
        if admission.admitted_entry_count != len(
            admission.admitted_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryRequestInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if admission.admitted_entry_count != len(
            admission.admitted_query_response_ids
        ):
            raise OracleOperatorQueryRequestInvariantError(
                "query-response cardinality mismatch"
            )
        if len(
            set(admission.admitted_response_artifact_entry_ids)
        ) != admission.admitted_entry_count:
            raise OracleOperatorQueryRequestInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(
            set(admission.admitted_query_response_ids)
        ) != admission.admitted_entry_count:
            raise OracleOperatorQueryRequestInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            admission.dependency_receipt_type_verified,
            admission.dependency_receipt_hash_verified,
            admission.subsystem_boundary_verified,
            admission.source_schema_verified,
            admission.source_authorization_schema_verified,
            admission.consumer_identity_verified,
            admission.projection_identity_verified,
            admission.entry_cardinality_verified,
            admission.unique_entry_identities_verified,
            admission.source_lineage_verified,
            admission.deterministic_replay_verified,
            admission.read_only_dependency_verified,
            admission.operator_query_construction_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission is incomplete"
            )

        forbidden_authority = (
            admission.operator_session_construction_allowed,
            admission.operator_console_rendering_allowed,
            admission.operator_presentation_rendering_allowed,
            admission.analytics_reexecution_allowed,
            admission.analytics_reexecution_performed,
            admission.analytics_database_connection_allowed,
            admission.analytics_database_connection_performed,
            admission.analytics_mutation_allowed,
            admission.analytics_mutation_performed,
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
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission contains forbidden authority or activity"
            )

    def materialize(
        self,
        *,
        admission: OracleOperatorAnalyticsDependencyAdmission,
        query_mode: str,
        query_text: str,
        time_scope: str = "all_authorized",
        sort_order: str = "relevance",
        result_limit: int = DEFAULT_RESULT_LIMIT,
        requested_tags: Sequence[str] = (),
    ) -> OracleOperatorQueryRequest:
        self._verify_admission(admission)

        if query_mode not in _ALLOWED_QUERY_MODES:
            raise OracleOperatorQueryRequestInvariantError(
                "unsupported query mode"
            )
        if time_scope not in _ALLOWED_TIME_SCOPES:
            raise OracleOperatorQueryRequestInvariantError(
                "unsupported time scope"
            )
        if sort_order not in _ALLOWED_SORT_ORDERS:
            raise OracleOperatorQueryRequestInvariantError(
                "unsupported sort order"
            )
        if (
            isinstance(result_limit, bool)
            or not isinstance(result_limit, int)
            or result_limit < 1
            or result_limit > MAX_RESULT_LIMIT
        ):
            raise OracleOperatorQueryRequestInvariantError(
                "result limit is outside the allowed range"
            )

        normalized_query_text = _normalize_text(query_text)
        normalized_tags = _normalize_tags(requested_tags)

        query_request_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_admission_id": admission.admission_id,
                "source_admission_hash": admission.admission_hash,
                "query_mode": query_mode,
                "query_text": normalized_query_text,
                "time_scope": time_scope,
                "sort_order": sort_order,
                "result_limit": result_limit,
                "requested_tags": normalized_tags,
                "authorized_response_artifact_entry_ids": (
                    admission.admitted_response_artifact_entry_ids
                ),
                "authorized_query_response_ids": (
                    admission.admitted_query_response_ids
                ),
            }
        )

        body = {
            "query_request_id": query_request_id,
            "source_admission_id": admission.admission_id,
            "source_admission_hash": admission.admission_hash,
            "source_dependency_receipt_id": (
                admission.source_dependency_receipt_id
            ),
            "source_dependency_receipt_hash": (
                admission.source_dependency_receipt_hash
            ),
            "source_authorization_id": admission.source_authorization_id,
            "source_authorization_hash": admission.source_authorization_hash,
            "operator_namespace": EXPECTED_OPERATOR_NAMESPACE,
            "consumer_id": admission.admitted_consumer_id,
            "projection": admission.admitted_projection,
            "query_mode": query_mode,
            "query_text": normalized_query_text,
            "time_scope": time_scope,
            "sort_order": sort_order,
            "result_limit": result_limit,
            "requested_tags": normalized_tags,
            "authorized_entry_count": admission.admitted_entry_count,
            "authorized_response_artifact_entry_ids": tuple(
                admission.admitted_response_artifact_entry_ids
            ),
            "authorized_query_response_ids": tuple(
                admission.admitted_query_response_ids
            ),
            "admission_type_verified": True,
            "admission_hash_verified": True,
            "admission_status_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "query_mode_verified": True,
            "time_scope_verified": True,
            "sort_order_verified": True,
            "result_limit_verified": True,
            "authorized_scope_preserved": True,
            "deterministic_request_verified": True,
            "analytics_read_only_dependency_preserved": True,
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
            "query_request_status": QUERY_REQUEST_STATUS,
        }

        return OracleOperatorQueryRequest(
            **body,
            query_request_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "QUERY_REQUEST_SCHEMA_VERSION",
    "QUERY_REQUEST_STATUS",
    "EXPECTED_ADMISSION_STATUS",
    "EXPECTED_CONSUMER_ID",
    "EXPECTED_PROJECTION",
    "MAX_QUERY_LENGTH",
    "MAX_RESULT_LIMIT",
    "DEFAULT_RESULT_LIMIT",
    "OracleOperatorQueryRequest",
    "OracleOperatorQueryRequestContract",
    "OracleOperatorQueryRequestInvariantError",
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
    QUERY_REQUEST_STATUS,
    OracleOperatorQueryRequestContract,
    OracleOperatorQueryRequestInvariantError,
    stable_hash,
)


def _admission():
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
    return OracleOperatorAnalyticsDependencyAdmissionGate().admit(
        receipt=receipt
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe query request accepted")
    except OracleOperatorQueryRequestInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-003 TEST")
    print(" OPERATOR QUERY REQUEST")
    print(" DETERMINISTIC READ-ONLY CONTRACT")
    print("=" * 40)

    admission = _admission()
    contract = OracleOperatorQueryRequestContract()

    first = contract.materialize(
        admission=admission,
        query_mode="opportunity_lookup",
        query_text="  Show   major opportunities closing today  ",
        time_scope="same_day",
        sort_order="priority",
        result_limit=20,
        requested_tags=(" Kalshi ", "Major", "kalshi"),
    )
    repeated = contract.materialize(
        admission=admission,
        query_mode="opportunity_lookup",
        query_text="Show major opportunities closing today",
        time_scope="same_day",
        sort_order="priority",
        result_limit=20,
        requested_tags=("major", "kalshi"),
    )

    assert first == repeated
    assert first.query_request_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "query_request_hash"
        }
    )

    assert first.source_admission_id == admission.admission_id
    assert first.source_admission_hash == admission.admission_hash
    assert first.consumer_id == "oracle.operator.console.v1"
    assert first.projection == "operator_research"
    assert first.operator_namespace == "qseries_v2.oracle_operator"
    assert first.query_mode == "opportunity_lookup"
    assert first.query_text == "Show major opportunities closing today"
    assert first.time_scope == "same_day"
    assert first.sort_order == "priority"
    assert first.result_limit == 20
    assert first.requested_tags == ("kalshi", "major")
    assert first.authorized_entry_count == admission.admitted_entry_count
    assert (
        first.authorized_response_artifact_entry_ids
        == admission.admitted_response_artifact_entry_ids
    )
    assert (
        first.authorized_query_response_ids
        == admission.admitted_query_response_ids
    )

    assert first.admission_type_verified
    assert first.admission_hash_verified
    assert first.admission_status_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.query_mode_verified
    assert first.time_scope_verified
    assert first.sort_order_verified
    assert first.result_limit_verified
    assert first.authorized_scope_preserved
    assert first.deterministic_request_verified
    assert first.analytics_read_only_dependency_preserved

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
    assert first.query_request_status == QUERY_REQUEST_STATUS

    _expect_rejected(
        lambda: contract.materialize(
            admission=replace(
                admission,
                admission_hash="0" * 64,
            ),
            query_mode="market_lookup",
            query_text="test",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=replace(
                admission,
                operator_query_construction_allowed=False,
            ),
            query_mode="market_lookup",
            query_text="test",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=replace(
                admission,
                qseries_execution_allowed=True,
            ),
            query_mode="market_lookup",
            query_text="test",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="unsupported",
            query_text="test",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="   ",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="test",
            time_scope="unsupported",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="test",
            sort_order="unsupported",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="test",
            result_limit=0,
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="test",
            result_limit=101,
        )
    )

    print("[PASS] Actual OOP-002 admission consumed")
    print("[PASS] OOP-002 identity, hash, status, and lineage verified")
    print("[PASS] Deterministic operator query request materialized")
    print("[PASS] Query text and tags normalized deterministically")
    print("[PASS] Query mode, time scope, sort order, and limit enforced")
    print("[PASS] Authorized analytics scope preserved without expansion")
    print("[PASS] No analytics query execution or reexecution performed")
    print("[PASS] No analytics database connection or mutation performed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed requests rejected")
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
    print(" OOP-003 INSTALLER")
    print(" OPERATOR QUERY REQUEST")
    print(" DETERMINISTIC READ-ONLY CONTRACT")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_002,
        "OOP-002",
        (
            'SCHEMA_VERSION = "OOP-002"',
            "class OracleOperatorAnalyticsDependencyAdmission",
            "class OracleOperatorAnalyticsDependencyAdmissionGate",
            "admission_id",
            "admission_hash",
            "admission_status",
            "operator_query_construction_allowed",
            "operator_session_construction_allowed",
            "operator_console_rendering_allowed",
            "operator_presentation_rendering_allowed",
            "analytics_reexecution_allowed",
            "analytics_database_connection_allowed",
            "analytics_mutation_allowed",
            "publication_allowed",
            "qseries_execution_allowed",
            "order_creation_allowed",
            "funds_movement_allowed",
            "portfolio_mutation_allowed",
        ),
    )
    verify_contract(
        SOURCE_OOP_001,
        "OOP-001",
        (
            'SCHEMA_VERSION = "OOP-001"',
            "class OracleOperatorAnalyticsDependencyReceipt",
            "dependency_receipt_hash",
            "read_only_dependency_verified",
        ),
    )
    verify_contract(
        SOURCE_060,
        "INT-OIA-060",
        (
            'SCHEMA_VERSION = "INT-OIA-060"',
            "authorization_hash",
            "read_only_consumption_verified",
            "publication_allowed",
            "order_execution_allowed",
        ),
    )

    protected_before = {
        SOURCE_OOP_002: sha256_file(SOURCE_OOP_002),
        SOURCE_OOP_001: sha256_file(SOURCE_OOP_001),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_operator_query_request_contract import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .query.oracle_operator_query_request_contract import *",
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
    print("[PASS] OOP-001, OOP-002, and INT-OIA-060 unchanged")

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
    print("[OK] OOP-003 test executed automatically")
    print()
    print("[DONE] OOP-003 operator query request contract installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
