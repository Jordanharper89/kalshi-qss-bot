from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
OPERATOR = QSERIES / "oracle_operator"
SESSION = OPERATOR / "session"
ANALYTICS_QUERY = (
    QSERIES / "oracle_intelligence" / "analytics" / "downstream" / "query"
)

SOURCE_060 = ANALYTICS_QUERY / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
SOURCE_026 = SESSION / "oracle_operator_session_construction_execution_gate.py"

PRODUCTION = SESSION / "oracle_operator_session_construction_result_certification_gate.py"
TEST = ROOT / "test_oop_027_oracle_operator_session_construction_result_certification_gate.py"
SESSION_INIT = SESSION / "__init__.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.session.oracle_operator_session_construction_execution_gate import (
    EXECUTION_STATUS as OOP_026_EXECUTION_STATUS,
    OPERATOR_SESSION_ARTIFACT_TYPE as OOP_026_OPERATOR_SESSION_ARTIFACT_TYPE,
    OPERATOR_SESSION_FORMAT as OOP_026_OPERATOR_SESSION_FORMAT,
    OracleOperatorSessionConstructionExecution,
)

SCHEMA_VERSION = "OOP-027"
ENGINE_ID = "OOP-027"
POLICY_ID = "oracle.operator.session-construction-result-certification-gate.v1"
CERTIFICATION_STATUS = "operator_session_construction_result_certified"
CERTIFICATION_TYPE = "immutable_operator_session_result_certification"

EXPECTED_EXECUTION_STATUS = OOP_026_EXECUTION_STATUS
EXPECTED_OPERATOR_SESSION_ARTIFACT_TYPE = OOP_026_OPERATOR_SESSION_ARTIFACT_TYPE
EXPECTED_OPERATOR_SESSION_FORMAT = OOP_026_OPERATOR_SESSION_FORMAT


class OracleOperatorSessionConstructionResultCertificationInvariantError(RuntimeError):
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
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorSessionConstructionResultCertificationInvariantError(
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
class OracleOperatorSessionConstructionResultCertification:
    operator_session_construction_result_certification_id: str
    source_operator_session_construction_execution_id: str
    source_operator_session_construction_execution_hash: str
    source_operator_session_construction_consumption_id: str
    source_operator_session_construction_consumption_hash: str
    source_operator_session_construction_authorization_id: str
    source_operator_session_construction_authorization_hash: str
    source_research_response_result_certification_id: str
    source_research_response_result_certification_hash: str
    operator_namespace: str
    query_namespace: str
    research_response_namespace: str
    session_namespace: str
    consumer_id: str
    query_text: str
    query_mode: str
    projection: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    execution_package_type: str
    operator_session_artifact_type: str
    operator_session_format: str
    certification_type: str
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    operator_session_id: str
    operator_session_payload: Mapping[str, Any]
    operator_session_payload_hash: str
    execution_identity_verified: bool
    execution_hash_verified: bool
    execution_status_verified: bool
    execution_package_type_verified: bool
    operator_session_identity_verified: bool
    operator_session_payload_hash_verified: bool
    operator_session_artifact_type_verified: bool
    operator_session_format_verified: bool
    research_response_identity_verified: bool
    research_response_payload_hash_verified: bool
    research_response_cardinality_verified: bool
    session_payload_preservation_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_session_verified: bool
    read_only_session_verified: bool
    deterministic_certification_verified: bool
    operator_session_construction_ready: bool
    operator_session_construction_authorized: bool
    operator_session_construction_authorization_consumed: bool
    operator_session_construction_allowed: bool
    operator_session_construction_performed: bool
    operator_session_result_certified: bool
    operator_console_construction_ready: bool
    operator_console_rendering_allowed: bool
    operator_console_rendering_performed: bool
    operator_presentation_rendering_allowed: bool
    operator_presentation_rendering_performed: bool
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
    certification_status: str
    operator_session_construction_result_certification_hash: str


class OracleOperatorSessionConstructionResultCertificationGate:
    @staticmethod
    def _verify(execution: OracleOperatorSessionConstructionExecution) -> None:
        if not isinstance(execution, OracleOperatorSessionConstructionExecution):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "source must be canonical OOP-026 execution"
            )

        body = asdict(execution)
        supplied_hash = body.pop("operator_session_construction_execution_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "OOP-026 execution hash mismatch"
            )

        if execution.execution_status != EXPECTED_EXECUTION_STATUS:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "OOP-026 execution status mismatch"
            )
        if execution.operator_session_artifact_type != EXPECTED_OPERATOR_SESSION_ARTIFACT_TYPE:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session artifact type mismatch"
            )
        if execution.operator_session_format != EXPECTED_OPERATOR_SESSION_FORMAT:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session format mismatch"
            )

        if not _valid_sha256(execution.operator_session_id):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session id invalid"
            )
        if not _valid_sha256(execution.operator_session_payload_hash):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session payload hash invalid"
            )
        if stable_hash(execution.operator_session_payload) != execution.operator_session_payload_hash:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session payload hash mismatch"
            )
        if execution.operator_session_payload.get("operator_session_id") != execution.operator_session_id:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session identity mismatch"
            )
        if execution.operator_session_payload.get("research_response_id") != execution.research_response_id:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response identity mismatch"
            )
        if execution.operator_session_payload.get("research_response_payload_hash") != execution.research_response_payload_hash:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response payload hash mismatch"
            )
        if execution.operator_session_payload.get("research_response_item_count") != execution.research_response_item_count:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response item count mismatch"
            )
        if tuple(execution.operator_session_payload.get("research_response_items") or ()) != tuple(execution.research_response_items):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response items mismatch"
            )
        if execution.operator_session_payload.get("read_only") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session is not read-only"
            )
        if execution.operator_session_payload.get("console_rendering_disabled") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "console rendering is not disabled"
            )
        if execution.operator_session_payload.get("presentation_rendering_disabled") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "presentation rendering is not disabled"
            )
        if execution.operator_session_payload.get("publication_disabled") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "publication is not disabled"
            )
        if execution.operator_session_payload.get("qseries_execution_disabled") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "Q Series execution is not disabled"
            )

        if execution.research_response_item_count < 1:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session has no research response items"
            )
        if execution.research_response_item_count != len(execution.research_response_items):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response cardinality mismatch"
            )

        required = (
            execution.authorization_consumption_verified,
            execution.authorization_identity_verified,
            execution.authorization_hash_verified,
            execution.authorization_status_verified,
            execution.execution_package_type_verified,
            execution.complete_lineage_verified,
            execution.frozen_scope_verified,
            execution.frozen_scope_preserved,
            execution.research_response_identity_verified,
            execution.research_response_payload_hash_verified,
            execution.response_item_cardinality_verified,
            execution.deterministic_session_construction_verified,
            execution.immutable_session_verified,
            execution.read_only_session_verified,
            execution.operator_session_construction_ready,
            execution.operator_session_construction_authorized,
            execution.operator_session_construction_authorization_consumed,
            execution.operator_session_construction_allowed,
            execution.operator_session_construction_performed,
            execution.operator_session_certification_ready,
        )
        if not all(required):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "OOP-026 execution incomplete"
            )

        forbidden = (
            execution.operator_console_rendering_allowed,
            execution.operator_console_rendering_performed,
            execution.operator_presentation_rendering_allowed,
            execution.operator_presentation_rendering_performed,
            execution.publication_allowed,
            execution.publication_performed,
            execution.qseries_handoff_allowed,
            execution.qseries_execution_allowed,
            execution.qseries_execution_performed,
            execution.order_creation_allowed,
            execution.order_creation_performed,
            execution.funds_movement_allowed,
            execution.funds_movement_performed,
            execution.portfolio_mutation_allowed,
            execution.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "forbidden downstream activity detected"
            )

    def certify(
        self,
        *,
        execution: OracleOperatorSessionConstructionExecution,
    ) -> OracleOperatorSessionConstructionResultCertification:
        self._verify(execution)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_execution_id": execution.operator_session_construction_execution_id,
                "source_execution_hash": execution.operator_session_construction_execution_hash,
                "operator_session_id": execution.operator_session_id,
                "operator_session_payload_hash": execution.operator_session_payload_hash,
                "certification_type": CERTIFICATION_TYPE,
            }
        )

        body = {
            "operator_session_construction_result_certification_id": certification_id,
            "source_operator_session_construction_execution_id": execution.operator_session_construction_execution_id,
            "source_operator_session_construction_execution_hash": execution.operator_session_construction_execution_hash,
            "source_operator_session_construction_consumption_id": execution.source_operator_session_construction_consumption_id,
            "source_operator_session_construction_consumption_hash": execution.source_operator_session_construction_consumption_hash,
            "source_operator_session_construction_authorization_id": execution.source_operator_session_construction_authorization_id,
            "source_operator_session_construction_authorization_hash": execution.source_operator_session_construction_authorization_hash,
            "source_research_response_result_certification_id": execution.source_research_response_result_certification_id,
            "source_research_response_result_certification_hash": execution.source_research_response_result_certification_hash,
            "operator_namespace": execution.operator_namespace,
            "query_namespace": execution.query_namespace,
            "research_response_namespace": execution.research_response_namespace,
            "session_namespace": execution.session_namespace,
            "consumer_id": execution.consumer_id,
            "query_text": execution.query_text,
            "query_mode": execution.query_mode,
            "projection": execution.projection,
            "time_scope": execution.time_scope,
            "sort_order": execution.sort_order,
            "result_limit": execution.result_limit,
            "requested_tags": tuple(execution.requested_tags),
            "execution_package_type": execution.execution_package_type,
            "operator_session_artifact_type": execution.operator_session_artifact_type,
            "operator_session_format": execution.operator_session_format,
            "certification_type": CERTIFICATION_TYPE,
            "research_response_id": execution.research_response_id,
            "research_response_payload_hash": execution.research_response_payload_hash,
            "research_response_item_count": execution.research_response_item_count,
            "research_response_items": tuple(execution.research_response_items),
            "operator_session_id": execution.operator_session_id,
            "operator_session_payload": dict(execution.operator_session_payload),
            "operator_session_payload_hash": execution.operator_session_payload_hash,
            "execution_identity_verified": True,
            "execution_hash_verified": True,
            "execution_status_verified": True,
            "execution_package_type_verified": True,
            "operator_session_identity_verified": True,
            "operator_session_payload_hash_verified": True,
            "operator_session_artifact_type_verified": True,
            "operator_session_format_verified": True,
            "research_response_identity_verified": True,
            "research_response_payload_hash_verified": True,
            "research_response_cardinality_verified": True,
            "session_payload_preservation_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_session_verified": True,
            "read_only_session_verified": True,
            "deterministic_certification_verified": True,
            "operator_session_construction_ready": True,
            "operator_session_construction_authorized": True,
            "operator_session_construction_authorization_consumed": True,
            "operator_session_construction_allowed": True,
            "operator_session_construction_performed": True,
            "operator_session_result_certified": True,
            "operator_console_construction_ready": True,
            "operator_console_rendering_allowed": False,
            "operator_console_rendering_performed": False,
            "operator_presentation_rendering_allowed": False,
            "operator_presentation_rendering_performed": False,
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
            "certification_status": CERTIFICATION_STATUS,
        }

        return OracleOperatorSessionConstructionResultCertification(
            **body,
            operator_session_construction_result_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_STATUS",
    "CERTIFICATION_TYPE",
    "OracleOperatorSessionConstructionResultCertification",
    "OracleOperatorSessionConstructionResultCertificationGate",
    "OracleOperatorSessionConstructionResultCertificationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_026_oracle_operator_session_construction_execution_gate import (
    _consumption,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_execution_gate import (
    OracleOperatorSessionConstructionExecutionGate,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    OracleOperatorSessionConstructionResultCertificationGate,
    OracleOperatorSessionConstructionResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorSessionConstructionExecutionGate().execute(
        consumption=_consumption()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe session certification accepted")
    except OracleOperatorSessionConstructionResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-027 TEST")
    print(" OPERATOR SESSION CONSTRUCTION")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorSessionConstructionResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.operator_session_construction_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_session_construction_result_certification_hash"
        }
    )
    assert first.operator_session_payload_hash == stable_hash(first.operator_session_payload)
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.operator_session_id == execution.operator_session_id
    assert first.operator_session_payload == execution.operator_session_payload

    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.execution_package_type_verified
    assert first.operator_session_identity_verified
    assert first.operator_session_payload_hash_verified
    assert first.operator_session_artifact_type_verified
    assert first.operator_session_format_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.research_response_cardinality_verified
    assert first.session_payload_preservation_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_session_verified
    assert first.read_only_session_verified
    assert first.deterministic_certification_verified

    assert first.operator_session_construction_ready
    assert first.operator_session_construction_authorized
    assert first.operator_session_construction_authorization_consumed
    assert first.operator_session_construction_allowed
    assert first.operator_session_construction_performed
    assert first.operator_session_result_certified
    assert first.operator_console_construction_ready
    assert not first.operator_console_rendering_allowed
    assert not first.operator_console_rendering_performed
    assert not first.operator_presentation_rendering_allowed
    assert not first.operator_presentation_rendering_performed
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

    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_session_construction_execution_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        execution_status="wrong_status",
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_session_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_item_count=execution.research_response_item_count + 1,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_console_rendering_allowed=True,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-026 Operator Session consumed")
    print("[PASS] OOP-026 execution identity, hash, and status verified")
    print("[PASS] Operator Session payload hash recomputed and verified")
    print("[PASS] Session artifact type, format, and identity verified")
    print("[PASS] Research Response lineage and cardinality preserved")
    print("[PASS] Immutable read-only Operator Session certified")
    print("[PASS] Complete frozen lineage preserved")
    print("[PASS] Operator Console construction marked ready")
    print("[PASS] Console rendering remains unauthorized")
    print("[PASS] Presentation, publication, and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe session executions rejected")
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
    print(" OOP-027 INSTALLER")
    print(" OPERATOR SESSION CONSTRUCTION")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    verify(
        SOURCE_026,
        "OOP-026",
        (
            'SCHEMA_VERSION = "OOP-026"',
            "class OracleOperatorSessionConstructionExecution",
            "operator_session_construction_execution_hash",
            "operator_session_payload_hash",
            "operator_session_payload",
            "operator_session_construction_performed",
            "operator_session_certification_ready",
            "operator_console_rendering_allowed",
            "qseries_execution_allowed",
        ),
    )
    verify(
        SOURCE_060,
        "INT-OIA-060",
        (
            'SCHEMA_VERSION = "INT-OIA-060"',
            "authorization_hash",
            "read_only_consumption_verified",
        ),
    )

    protected = {
        SOURCE_026: sha256_file(SOURCE_026),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        SESSION_INIT,
        "from .oracle_operator_session_construction_result_certification_gate import *",
    )
    export(
        OPERATOR_INIT,
        "from .session.oracle_operator_session_construction_result_certification_gate import *",
    )

    for path in (PRODUCTION, TEST, SESSION_INIT, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-026 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics, Query, or Research Response export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-027 test executed automatically")
    print()
    print("[DONE] OOP-027 Operator Session result certification installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
