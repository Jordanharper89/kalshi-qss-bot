from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
RUNTIME = QSERIES / "oracle_operator_runtime"
SOURCE_001 = RUNTIME / "oracle_operator_runtime_certified_read_only_dependency_gate.py"
PRODUCTION = RUNTIME / "oracle_operator_runtime_request_contract.py"
TEST = ROOT / "test_oor_002_oracle_operator_runtime_request_contract.py"
RUNTIME_INIT = RUNTIME / "__init__.py"

PRODUCTION_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_certified_read_only_dependency_gate import (
    DEPENDENCY_STATUS as OOR_001_DEPENDENCY_STATUS,
    DEPENDENCY_TYPE as OOR_001_DEPENDENCY_TYPE,
    RUNTIME_NAMESPACE,
    OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt,
)

SCHEMA_VERSION = "OOR-002"
ENGINE_ID = "OOR-002"
POLICY_ID = "oracle.operator-runtime-request-contract.v1"
REQUEST_TYPE = "oracle_operator_runtime_read_only_request"
REQUEST_STATUS = "oracle_operator_runtime_request_materialized"
CONSUMER_ID = "oracle.operator.runtime.v1"
PROJECTION = "certified_operator_read_only"

_ALLOWED_MODES = frozenset({"query", "session", "console", "presentation"})
_TOKEN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")


class OracleOperatorRuntimeRequestInvariantError(ValueError):
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
            raise OracleOperatorRuntimeRequestInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeRequestInvariantError(
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


def _clean_text(value: Any, *, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise OracleOperatorRuntimeRequestInvariantError(f"{field} must be a string")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > maximum:
        raise OracleOperatorRuntimeRequestInvariantError(
            f"{field} must contain 1 through {maximum} normalized characters"
        )
    return cleaned


@dataclass(frozen=True)
class OracleOperatorRuntimeRequest:
    request_id: str
    dependency_receipt_id: str
    dependency_receipt_hash: str
    source_operator_completion_certification_id: str
    runtime_namespace: str
    requester_id: str
    correlation_id: str
    mode: str
    query_text: str
    requested_at: datetime
    read_only_required: bool
    deterministic_required: bool
    immutable_result_required: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    request_type: str
    request_status: str
    request_hash: str


class OracleOperatorRuntimeRequestContract:
    @staticmethod
    def _verify_dependency(
        receipt: OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt,
    ) -> None:
        if not isinstance(receipt, OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt):
            raise OracleOperatorRuntimeRequestInvariantError(
                "dependency must be canonical OOR-001 receipt"
            )
        body = asdict(receipt)
        supplied_hash = body.pop("dependency_receipt_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeRequestInvariantError(
                "OOR-001 dependency receipt hash mismatch"
            )
        required = (
            receipt.dependency_status == OOR_001_DEPENDENCY_STATUS,
            receipt.dependency_type == OOR_001_DEPENDENCY_TYPE,
            receipt.runtime_namespace == RUNTIME_NAMESPACE,
            receipt.consumer_id == CONSUMER_ID,
            receipt.projection == PROJECTION,
            receipt.source_operator_subsystem_completion_certified,
            receipt.source_operator_subsystem_frozen,
            not receipt.source_further_operator_builds_required,
            receipt.certification_hash_verified,
            receipt.freeze_record_payload_hash_verified,
            receipt.complete_operator_lineage_verified,
            receipt.operator_completion_verified,
            receipt.operator_freeze_verified,
            receipt.deterministic_dependency_verified,
            receipt.immutable_dependency_verified,
            receipt.read_only_dependency_verified,
            receipt.runtime_subsystem_root_established,
        )
        if not all(required):
            raise OracleOperatorRuntimeRequestInvariantError(
                "OOR-001 dependency receipt is incomplete"
            )
        forbidden = (
            receipt.runtime_serving_allowed,
            receipt.runtime_serving_performed,
            receipt.network_listener_allowed,
            receipt.network_listener_started,
            receipt.operator_reexecution_allowed,
            receipt.operator_reexecution_performed,
            receipt.analytics_reexecution_allowed,
            receipt.analytics_reexecution_performed,
            receipt.database_connection_allowed,
            receipt.database_connection_performed,
            receipt.publication_allowed,
            receipt.publication_performed,
            receipt.qseries_handoff_allowed,
            receipt.qseries_execution_allowed,
            receipt.qseries_execution_performed,
            receipt.order_creation_allowed,
            receipt.order_creation_performed,
            receipt.funds_movement_allowed,
            receipt.funds_movement_performed,
            receipt.portfolio_mutation_allowed,
            receipt.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeRequestInvariantError(
                "forbidden OOR-001 dependency state detected"
            )

    def materialize(
        self,
        *,
        dependency_receipt: OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt,
        requester_id: str,
        correlation_id: str,
        mode: str,
        query_text: str,
        requested_at: datetime,
    ) -> OracleOperatorRuntimeRequest:
        self._verify_dependency(dependency_receipt)

        requester = _clean_text(requester_id, field="requester_id", maximum=128)
        correlation = _clean_text(correlation_id, field="correlation_id", maximum=128)
        if not _TOKEN.fullmatch(requester):
            raise OracleOperatorRuntimeRequestInvariantError("requester_id is not canonical")
        if not _TOKEN.fullmatch(correlation):
            raise OracleOperatorRuntimeRequestInvariantError("correlation_id is not canonical")
        if mode not in _ALLOWED_MODES:
            raise OracleOperatorRuntimeRequestInvariantError("unsupported runtime request mode")
        query = _clean_text(query_text, field="query_text", maximum=4096)
        if not isinstance(requested_at, datetime) or requested_at.tzinfo is None or requested_at.utcoffset() is None:
            raise OracleOperatorRuntimeRequestInvariantError(
                "requested_at must be timezone-aware"
            )
        normalized_time = requested_at.astimezone(timezone.utc)

        request_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "dependency_receipt_id": dependency_receipt.dependency_receipt_id,
                "dependency_receipt_hash": dependency_receipt.dependency_receipt_hash,
                "requester_id": requester,
                "correlation_id": correlation,
                "mode": mode,
                "query_text": query,
                "requested_at": normalized_time,
                "request_type": REQUEST_TYPE,
            }
        )
        body = {
            "request_id": request_id,
            "dependency_receipt_id": dependency_receipt.dependency_receipt_id,
            "dependency_receipt_hash": dependency_receipt.dependency_receipt_hash,
            "source_operator_completion_certification_id": dependency_receipt.source_operator_completion_certification_id,
            "runtime_namespace": RUNTIME_NAMESPACE,
            "requester_id": requester,
            "correlation_id": correlation,
            "mode": mode,
            "query_text": query,
            "requested_at": normalized_time,
            "read_only_required": True,
            "deterministic_required": True,
            "immutable_result_required": True,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "request_type": REQUEST_TYPE,
            "request_status": REQUEST_STATUS,
        }
        return OracleOperatorRuntimeRequest(
            **body,
            request_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "REQUEST_TYPE",
    "REQUEST_STATUS",
    "CONSUMER_ID",
    "PROJECTION",
    "OracleOperatorRuntimeRequest",
    "OracleOperatorRuntimeRequestContract",
    "OracleOperatorRuntimeRequestInvariantError",
    "stable_hash",
]
'''

TEST_SOURCE = r'''from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_certified_read_only_dependency_gate import (
    DEPENDENCY_STATUS,
    DEPENDENCY_TYPE,
    RUNTIME_NAMESPACE,
    OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt,
    stable_hash as dependency_hash,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_request_contract import (
    REQUEST_STATUS,
    REQUEST_TYPE,
    OracleOperatorRuntimeRequestContract,
    OracleOperatorRuntimeRequestInvariantError,
    stable_hash,
)


def _dependency():
    body = {
        "dependency_receipt_id": dependency_hash({"receipt": "oor-001-test"}),
        "source_operator_completion_certification_id": dependency_hash({"certification": "oop-047"}),
        "source_operator_completion_certification_hash": dependency_hash({"certification_hash": "oop-047"}),
        "source_freeze_record_id": dependency_hash({"freeze": "oop-047"}),
        "source_freeze_record_payload_hash": dependency_hash({"freeze_payload": "oop-047"}),
        "source_certification_status": "oracle_operator_subsystem_completion_certified",
        "source_certification_type": "terminal_read_only_oracle_operator_subsystem_completion_certification",
        "source_freeze_record_type": "immutable_oracle_operator_subsystem_completion_freeze_record",
        "runtime_namespace": RUNTIME_NAMESPACE,
        "operator_namespace": "qseries_v2.oracle_operator",
        "qseries_execution_namespace": "qseries_v2.execution",
        "consumer_id": "oracle.operator.runtime.v1",
        "projection": "certified_operator_read_only",
        "source_query_boundary_complete": True,
        "source_research_response_boundary_complete": True,
        "source_session_boundary_complete": True,
        "source_console_boundary_complete": True,
        "source_presentation_boundary_complete": True,
        "source_operator_subsystem_completion_ready": True,
        "source_operator_subsystem_completion_certified": True,
        "source_operator_subsystem_frozen": True,
        "source_further_operator_builds_required": False,
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
        dependency_receipt_hash=dependency_hash(body),
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe runtime request accepted")
    except OracleOperatorRuntimeRequestInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-002 TEST")
    print(" ORACLE OPERATOR RUNTIME REQUEST")
    print(" CANONICAL READ-ONLY CONTRACT")
    print("=" * 40)

    dependency = _dependency()
    contract = OracleOperatorRuntimeRequestContract()
    requested_at = datetime(2026, 7, 28, 3, 30, tzinfo=timezone.utc)

    first = contract.materialize(
        dependency_receipt=dependency,
        requester_id="operator.console",
        correlation_id="oracle-request-0001",
        mode="query",
        query_text="  Show the highest-priority certified opportunity.  ",
        requested_at=requested_at,
    )
    repeated = contract.materialize(
        dependency_receipt=dependency,
        requester_id="operator.console",
        correlation_id="oracle-request-0001",
        mode="query",
        query_text="Show the highest-priority certified opportunity.",
        requested_at=requested_at,
    )

    assert first == repeated
    assert first.request_type == REQUEST_TYPE
    assert first.request_status == REQUEST_STATUS
    assert first.runtime_namespace == RUNTIME_NAMESPACE
    assert first.query_text == "Show the highest-priority certified opportunity."
    assert first.requested_at == requested_at
    assert first.read_only_required
    assert first.deterministic_required
    assert first.immutable_result_required
    assert first.request_hash == stable_hash(
        {key: value for key, value in first.__dict__.items() if key != "request_hash"}
    )

    forbidden = (
        first.runtime_serving_allowed,
        first.network_listener_allowed,
        first.database_connection_allowed,
        first.publication_allowed,
        first.qseries_handoff_allowed,
        first.qseries_execution_allowed,
        first.order_creation_allowed,
        first.funds_movement_allowed,
        first.portfolio_mutation_allowed,
    )
    assert not any(forbidden)

    _reject(lambda: contract.materialize(
        dependency_receipt=replace(dependency, dependency_receipt_hash="0" * 64),
        requester_id="operator.console", correlation_id="oracle-request-0001",
        mode="query", query_text="test", requested_at=requested_at,
    ))
    _reject(lambda: contract.materialize(
        dependency_receipt=dependency, requester_id="operator console",
        correlation_id="oracle-request-0001", mode="query",
        query_text="test", requested_at=requested_at,
    ))
    _reject(lambda: contract.materialize(
        dependency_receipt=dependency, requester_id="operator.console",
        correlation_id="oracle-request-0001", mode="execute",
        query_text="test", requested_at=requested_at,
    ))
    _reject(lambda: contract.materialize(
        dependency_receipt=dependency, requester_id="operator.console",
        correlation_id="oracle-request-0001", mode="query",
        query_text="   ", requested_at=requested_at,
    ))
    _reject(lambda: contract.materialize(
        dependency_receipt=dependency, requester_id="operator.console",
        correlation_id="oracle-request-0001", mode="query",
        query_text="test", requested_at=datetime(2026, 7, 28, 3, 30),
    ))

    print("[PASS] Actual OOR-001 certified read-only receipt contract consumed")
    print("[PASS] Canonical runtime request identity and hash deterministic")
    print("[PASS] Query, session, console, and presentation modes bounded")
    print("[PASS] Request text normalized without changing meaning")
    print("[PASS] Immutable read-only runtime request materialized")
    print("[PASS] Runtime serving and network listener remain disabled")
    print("[PASS] Database connection and publication remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe requests rejected")
    print("[DONE] OOR-002 ORACLE OPERATOR RUNTIME REQUEST CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''



def _verify_oor_001() -> None:
    if not SOURCE_001.is_file():
        raise RuntimeError(f"Actual OOR-001 module missing: {SOURCE_001}")
    tree = ast.parse(SOURCE_001.read_text(encoding="utf-8"))
    names = {node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}
    required = {
        "OracleOperatorRuntimeCertifiedReadOnlyDependencyGate",
        "OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt",
        "stable_hash",
    }
    missing = sorted(required - names)
    if missing:
        raise RuntimeError(f"OOR-001 contract incomplete: {missing}")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8", newline="\n")


def main() -> int:
    print("=" * 40)
    print(" OOR-002 INSTALLER")
    print(" ORACLE OPERATOR RUNTIME REQUEST")
    print(" CANONICAL READ-ONLY CONTRACT")
    print("=" * 40)
    try:
        _verify_oor_001()
        print("[OK] Actual OOR-001 dependency contract verified")
        _write(PRODUCTION, PRODUCTION_SOURCE)
        _write(TEST, TEST_SOURCE)
        if not RUNTIME_INIT.exists():
            _write(RUNTIME_INIT, "from __future__ import annotations\n")
        print(f"[OK] FULL REPLACEMENT: {PRODUCTION}")
        print(f"[OK] FULL REPLACEMENT: {TEST}")
        subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=True)
        print("[DONE] OOR-002 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
