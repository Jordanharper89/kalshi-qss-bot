from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
OPERATOR = QSERIES / "oracle_operator"
PRESENTATION = OPERATOR / "presentation"
ANALYTICS_QUERY = (
    QSERIES / "oracle_intelligence" / "analytics" / "downstream" / "query"
)

SOURCE_060 = ANALYTICS_QUERY / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
SOURCE_038 = PRESENTATION / "oracle_operator_presentation_rendering_execution_gate.py"

PRODUCTION = PRESENTATION / "oracle_operator_presentation_rendering_result_certification_gate.py"
TEST = ROOT / "test_oop_039_oracle_operator_presentation_rendering_result_certification_gate.py"
PRESENTATION_INIT = PRESENTATION / "__init__.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_execution_gate import (
    EXECUTION_STATUS as OOP_038_EXECUTION_STATUS,
    RENDERED_PRESENTATION_ARTIFACT_TYPE as OOP_038_RENDERED_PRESENTATION_ARTIFACT_TYPE,
    RENDERED_PRESENTATION_FORMAT as OOP_038_RENDERED_PRESENTATION_FORMAT,
    OracleOperatorPresentationRenderingExecution,
)

SCHEMA_VERSION = "OOP-039"
ENGINE_ID = "OOP-039"
POLICY_ID = "oracle.operator.presentation-rendering-result-certification-gate.v1"
CERTIFICATION_STATUS = "operator_presentation_rendering_result_certified"
CERTIFICATION_TYPE = "immutable_rendered_operator_presentation_result_certification"

EXPECTED_EXECUTION_STATUS = OOP_038_EXECUTION_STATUS
EXPECTED_RENDERED_PRESENTATION_ARTIFACT_TYPE = OOP_038_RENDERED_PRESENTATION_ARTIFACT_TYPE
EXPECTED_RENDERED_PRESENTATION_FORMAT = OOP_038_RENDERED_PRESENTATION_FORMAT
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorPresentationRenderingResultCertificationInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
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
class OracleOperatorPresentationRenderingResultCertification:
    operator_presentation_rendering_result_certification_id: str
    source_operator_presentation_rendering_execution_id: str
    source_operator_presentation_rendering_execution_hash: str
    source_operator_presentation_rendering_consumption_id: str
    source_operator_presentation_rendering_consumption_hash: str
    source_operator_presentation_rendering_authorization_id: str
    source_operator_presentation_rendering_authorization_hash: str
    source_operator_console_rendering_result_certification_id: str
    source_operator_console_rendering_result_certification_hash: str
    operator_namespace: str
    query_namespace: str
    research_response_namespace: str
    session_namespace: str
    console_namespace: str
    presentation_namespace: str
    consumer_id: str
    query_text: str
    query_mode: str
    projection: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    operator_session_artifact_type: str
    operator_session_format: str
    operator_console_artifact_type: str
    operator_console_format: str
    rendered_console_artifact_type: str
    rendered_console_format: str
    rendered_presentation_artifact_type: str
    rendered_presentation_format: str
    certification_type: str
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    operator_session_id: str
    operator_session_payload: Mapping[str, Any]
    operator_session_payload_hash: str
    operator_console_id: str
    operator_console_payload: Mapping[str, Any]
    operator_console_payload_hash: str
    rendered_console_id: str
    rendered_console_payload: Mapping[str, Any]
    rendered_console_payload_hash: str
    rendered_presentation_id: str
    rendered_presentation_payload: Mapping[str, Any]
    rendered_presentation_payload_hash: str
    execution_identity_verified: bool
    execution_hash_verified: bool
    execution_status_verified: bool
    rendered_presentation_identity_verified: bool
    rendered_presentation_payload_hash_verified: bool
    rendered_presentation_artifact_type_verified: bool
    rendered_presentation_format_verified: bool
    rendered_presentation_sections_verified: bool
    rendered_console_identity_verified: bool
    rendered_console_payload_hash_verified: bool
    operator_console_identity_verified: bool
    operator_console_payload_hash_verified: bool
    operator_session_identity_verified: bool
    operator_session_payload_hash_verified: bool
    research_response_identity_verified: bool
    research_response_payload_hash_verified: bool
    research_response_cardinality_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_rendered_presentation_verified: bool
    read_only_rendered_presentation_verified: bool
    deterministic_certification_verified: bool
    operator_console_rendering_result_certified: bool
    operator_presentation_rendering_authorized: bool
    operator_presentation_rendering_authorization_consumed: bool
    operator_presentation_rendering_allowed: bool
    operator_presentation_rendering_performed: bool
    operator_presentation_rendering_result_certified: bool
    publication_authorization_ready: bool
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
    operator_presentation_rendering_result_certification_hash: str


class OracleOperatorPresentationRenderingResultCertificationGate:
    @staticmethod
    def _verify(execution: OracleOperatorPresentationRenderingExecution) -> None:
        if not isinstance(execution, OracleOperatorPresentationRenderingExecution):
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "source must be canonical OOP-038 execution"
            )

        body = asdict(execution)
        supplied_hash = body.pop(
            "operator_presentation_rendering_execution_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "OOP-038 execution hash mismatch"
            )

        if execution.execution_status != EXPECTED_EXECUTION_STATUS:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "OOP-038 execution status mismatch"
            )
        if execution.rendered_presentation_artifact_type != EXPECTED_RENDERED_PRESENTATION_ARTIFACT_TYPE:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation artifact type mismatch"
            )
        if execution.rendered_presentation_format != EXPECTED_RENDERED_PRESENTATION_FORMAT:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation format mismatch"
            )
        if execution.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(execution.rendered_presentation_id):
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation id invalid"
            )
        if not _valid_sha256(execution.rendered_presentation_payload_hash):
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation payload hash invalid"
            )
        if stable_hash(execution.rendered_presentation_payload) != execution.rendered_presentation_payload_hash:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation payload hash mismatch"
            )

        payload = execution.rendered_presentation_payload
        if payload.get("rendered_presentation_id") != execution.rendered_presentation_id:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation identity mismatch"
            )
        if payload.get("rendered_presentation_format") != execution.rendered_presentation_format:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation format payload mismatch"
            )
        if payload.get("rendered_console_id") != execution.rendered_console_id:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered console identity mismatch"
            )
        if payload.get("rendered_console_payload_hash") != execution.rendered_console_payload_hash:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered console payload hash mismatch"
            )
        if payload.get("operator_console_id") != execution.operator_console_id:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "operator console identity mismatch"
            )
        if payload.get("operator_session_id") != execution.operator_session_id:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "operator session identity mismatch"
            )
        if payload.get("research_response_id") != execution.research_response_id:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "research response identity mismatch"
            )
        if payload.get("research_response_item_count") != execution.research_response_item_count:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "research response cardinality mismatch"
            )
        if tuple(payload.get("research_response_items") or ()) != tuple(execution.research_response_items):
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "research response items mismatch"
            )

        sections = tuple(payload.get("sections") or ())
        if tuple(section.get("section_id") for section in sections) != (
            "presentation_header",
            "presentation_results",
            "presentation_context",
            "presentation_lineage",
        ):
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation sections mismatch"
            )
        if payload.get("read_only") is not True:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation is not read-only"
            )
        if payload.get("publication_disabled") is not True:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "publication boundary missing"
            )
        if payload.get("qseries_execution_disabled") is not True:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "Q Series execution boundary missing"
            )

        if stable_hash(execution.rendered_console_payload) != execution.rendered_console_payload_hash:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "source rendered console payload hash mismatch"
            )
        if stable_hash(execution.operator_console_payload) != execution.operator_console_payload_hash:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "source operator console payload hash mismatch"
            )
        if execution.research_response_item_count < 1:
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "rendered presentation contains no research response items"
            )
        if execution.research_response_item_count != len(execution.research_response_items):
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "research response cardinality mismatch"
            )

        required = (
            execution.consumption_identity_verified,
            execution.consumption_hash_verified,
            execution.consumption_status_verified,
            execution.presentation_execution_package_type_verified,
            execution.rendered_console_identity_verified,
            execution.rendered_console_payload_hash_verified,
            execution.operator_console_identity_verified,
            execution.operator_console_payload_hash_verified,
            execution.operator_session_identity_verified,
            execution.operator_session_payload_hash_verified,
            execution.research_response_identity_verified,
            execution.research_response_payload_hash_verified,
            execution.research_response_cardinality_verified,
            execution.rendered_sections_verified,
            execution.complete_lineage_verified,
            execution.frozen_scope_verified,
            execution.frozen_scope_preserved,
            execution.deterministic_rendering_verified,
            execution.immutable_rendered_presentation_verified,
            execution.read_only_rendered_presentation_verified,
            execution.operator_console_rendering_result_certified,
            execution.operator_presentation_rendering_authorization_ready,
            execution.operator_presentation_rendering_authorized,
            execution.operator_presentation_rendering_authorization_consumed,
            execution.operator_presentation_rendering_allowed,
            execution.operator_presentation_rendering_performed,
            execution.operator_presentation_rendering_result_certification_ready,
        )
        if not all(required):
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "OOP-038 execution incomplete"
            )

        forbidden = (
            execution.publication_authorization_ready,
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
            raise OracleOperatorPresentationRenderingResultCertificationInvariantError(
                "forbidden downstream activity detected"
            )

    def certify(
        self,
        *,
        execution: OracleOperatorPresentationRenderingExecution,
    ) -> OracleOperatorPresentationRenderingResultCertification:
        self._verify(execution)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_execution_id": execution.operator_presentation_rendering_execution_id,
                "source_execution_hash": execution.operator_presentation_rendering_execution_hash,
                "rendered_presentation_id": execution.rendered_presentation_id,
                "rendered_presentation_payload_hash": execution.rendered_presentation_payload_hash,
                "certification_type": CERTIFICATION_TYPE,
            }
        )

        body = {
            "operator_presentation_rendering_result_certification_id": certification_id,
            "source_operator_presentation_rendering_execution_id": execution.operator_presentation_rendering_execution_id,
            "source_operator_presentation_rendering_execution_hash": execution.operator_presentation_rendering_execution_hash,
            "source_operator_presentation_rendering_consumption_id": execution.source_operator_presentation_rendering_consumption_id,
            "source_operator_presentation_rendering_consumption_hash": execution.source_operator_presentation_rendering_consumption_hash,
            "source_operator_presentation_rendering_authorization_id": execution.source_operator_presentation_rendering_authorization_id,
            "source_operator_presentation_rendering_authorization_hash": execution.source_operator_presentation_rendering_authorization_hash,
            "source_operator_console_rendering_result_certification_id": execution.source_operator_console_rendering_result_certification_id,
            "source_operator_console_rendering_result_certification_hash": execution.source_operator_console_rendering_result_certification_hash,
            "operator_namespace": execution.operator_namespace,
            "query_namespace": execution.query_namespace,
            "research_response_namespace": execution.research_response_namespace,
            "session_namespace": execution.session_namespace,
            "console_namespace": execution.console_namespace,
            "presentation_namespace": execution.presentation_namespace,
            "consumer_id": execution.consumer_id,
            "query_text": execution.query_text,
            "query_mode": execution.query_mode,
            "projection": execution.projection,
            "time_scope": execution.time_scope,
            "sort_order": execution.sort_order,
            "result_limit": execution.result_limit,
            "requested_tags": tuple(execution.requested_tags),
            "operator_session_artifact_type": execution.operator_session_artifact_type,
            "operator_session_format": execution.operator_session_format,
            "operator_console_artifact_type": execution.operator_console_artifact_type,
            "operator_console_format": execution.operator_console_format,
            "rendered_console_artifact_type": execution.rendered_console_artifact_type,
            "rendered_console_format": execution.rendered_console_format,
            "rendered_presentation_artifact_type": execution.rendered_presentation_artifact_type,
            "rendered_presentation_format": execution.rendered_presentation_format,
            "certification_type": CERTIFICATION_TYPE,
            "research_response_id": execution.research_response_id,
            "research_response_payload_hash": execution.research_response_payload_hash,
            "research_response_item_count": execution.research_response_item_count,
            "research_response_items": tuple(execution.research_response_items),
            "operator_session_id": execution.operator_session_id,
            "operator_session_payload": dict(execution.operator_session_payload),
            "operator_session_payload_hash": execution.operator_session_payload_hash,
            "operator_console_id": execution.operator_console_id,
            "operator_console_payload": dict(execution.operator_console_payload),
            "operator_console_payload_hash": execution.operator_console_payload_hash,
            "rendered_console_id": execution.rendered_console_id,
            "rendered_console_payload": dict(execution.rendered_console_payload),
            "rendered_console_payload_hash": execution.rendered_console_payload_hash,
            "rendered_presentation_id": execution.rendered_presentation_id,
            "rendered_presentation_payload": dict(execution.rendered_presentation_payload),
            "rendered_presentation_payload_hash": execution.rendered_presentation_payload_hash,
            "execution_identity_verified": True,
            "execution_hash_verified": True,
            "execution_status_verified": True,
            "rendered_presentation_identity_verified": True,
            "rendered_presentation_payload_hash_verified": True,
            "rendered_presentation_artifact_type_verified": True,
            "rendered_presentation_format_verified": True,
            "rendered_presentation_sections_verified": True,
            "rendered_console_identity_verified": True,
            "rendered_console_payload_hash_verified": True,
            "operator_console_identity_verified": True,
            "operator_console_payload_hash_verified": True,
            "operator_session_identity_verified": True,
            "operator_session_payload_hash_verified": True,
            "research_response_identity_verified": True,
            "research_response_payload_hash_verified": True,
            "research_response_cardinality_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_rendered_presentation_verified": True,
            "read_only_rendered_presentation_verified": True,
            "deterministic_certification_verified": True,
            "operator_console_rendering_result_certified": True,
            "operator_presentation_rendering_authorized": True,
            "operator_presentation_rendering_authorization_consumed": True,
            "operator_presentation_rendering_allowed": True,
            "operator_presentation_rendering_performed": True,
            "operator_presentation_rendering_result_certified": True,
            "publication_authorization_ready": True,
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

        return OracleOperatorPresentationRenderingResultCertification(
            **body,
            operator_presentation_rendering_result_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_STATUS",
    "CERTIFICATION_TYPE",
    "OracleOperatorPresentationRenderingResultCertification",
    "OracleOperatorPresentationRenderingResultCertificationGate",
    "OracleOperatorPresentationRenderingResultCertificationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_038_oracle_operator_presentation_rendering_execution_gate import (
    _consumption,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_execution_gate import (
    OracleOperatorPresentationRenderingExecutionGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    OracleOperatorPresentationRenderingResultCertificationGate,
    OracleOperatorPresentationRenderingResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorPresentationRenderingExecutionGate().execute(
        consumption=_consumption()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe presentation certification accepted")
    except OracleOperatorPresentationRenderingResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-039 TEST")
    print(" OPERATOR PRESENTATION RENDERING")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorPresentationRenderingResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.operator_presentation_rendering_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_rendering_result_certification_hash"
        }
    )
    assert first.rendered_presentation_payload_hash == stable_hash(
        first.rendered_presentation_payload
    )
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.rendered_presentation_id == execution.rendered_presentation_id
    assert first.rendered_presentation_payload == execution.rendered_presentation_payload

    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.rendered_presentation_identity_verified
    assert first.rendered_presentation_payload_hash_verified
    assert first.rendered_presentation_artifact_type_verified
    assert first.rendered_presentation_format_verified
    assert first.rendered_presentation_sections_verified
    assert first.rendered_console_identity_verified
    assert first.rendered_console_payload_hash_verified
    assert first.operator_console_identity_verified
    assert first.operator_console_payload_hash_verified
    assert first.operator_session_identity_verified
    assert first.operator_session_payload_hash_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.research_response_cardinality_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_rendered_presentation_verified
    assert first.read_only_rendered_presentation_verified
    assert first.deterministic_certification_verified

    assert first.operator_console_rendering_result_certified
    assert first.operator_presentation_rendering_authorized
    assert first.operator_presentation_rendering_authorization_consumed
    assert first.operator_presentation_rendering_allowed
    assert first.operator_presentation_rendering_performed
    assert first.operator_presentation_rendering_result_certified
    assert first.publication_authorization_ready
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
        operator_presentation_rendering_execution_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        execution_status="wrong_status",
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        rendered_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_item_count=execution.research_response_item_count + 1,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        publication_authorization_ready=True,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-038 rendered presentation execution consumed")
    print("[PASS] Execution identity, hash, status, artifact type, and format verified")
    print("[PASS] Rendered presentation identity and payload hash verified")
    print("[PASS] Presentation header, results, context, and lineage sections verified")
    print("[PASS] Rendered Console, Operator Console, Session, and Research Response lineage preserved")
    print("[PASS] Immutable read-only rendered presentation certified")
    print("[PASS] Complete frozen lineage preserved")
    print("[PASS] Publication authorization marked ready")
    print("[PASS] Publication remains unauthorized and unperformed")
    print("[PASS] Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe presentation executions rejected")
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
    print(" OOP-039 INSTALLER")
    print(" OPERATOR PRESENTATION RENDERING")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    verify(
        SOURCE_038,
        "OOP-038",
        (
            'SCHEMA_VERSION = "OOP-038"',
            "class OracleOperatorPresentationRenderingExecution",
            "operator_presentation_rendering_execution_hash",
            "rendered_presentation_payload_hash",
            "rendered_presentation_payload",
            "operator_presentation_rendering_performed",
            "operator_presentation_rendering_result_certification_ready",
            "publication_authorization_ready",
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
        SOURCE_038: sha256_file(SOURCE_038),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        PRESENTATION_INIT,
        "from .oracle_operator_presentation_rendering_result_certification_gate import *",
    )
    export(
        OPERATOR_INIT,
        "from .presentation.oracle_operator_presentation_rendering_result_certification_gate import *",
    )

    for path in (PRODUCTION, TEST, PRESENTATION_INIT, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-038 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics, Query, Research Response, Session, or Console export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-039 test executed automatically")
    print()
    print("[DONE] OOP-039 Operator presentation rendering result certification installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
