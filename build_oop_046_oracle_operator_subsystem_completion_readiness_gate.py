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
SOURCE_045 = PRESENTATION / "oracle_operator_presentation_subsystem_completion_certification_gate.py"

PRODUCTION = OPERATOR / "oracle_operator_subsystem_completion_readiness_gate.py"
TEST = ROOT / "test_oop_046_oracle_operator_subsystem_completion_readiness_gate.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_subsystem_completion_certification_gate import (
    CERTIFICATION_STATUS as OOP_045_CERTIFICATION_STATUS,
    CERTIFICATION_TYPE as OOP_045_CERTIFICATION_TYPE,
    FREEZE_RECORD_TYPE as OOP_045_FREEZE_RECORD_TYPE,
    OracleOperatorPresentationSubsystemCompletionCertification,
)

SCHEMA_VERSION = "OOP-046"
ENGINE_ID = "OOP-046"
POLICY_ID = "oracle.operator-subsystem-completion-readiness-gate.v1"
READINESS_STATUS = "oracle_operator_subsystem_completion_ready"
READINESS_TYPE = "terminal_read_only_oracle_operator_subsystem_completion_readiness"
READINESS_RECORD_TYPE = "immutable_oracle_operator_subsystem_completion_readiness_record"

EXPECTED_CERTIFICATION_STATUS = OOP_045_CERTIFICATION_STATUS
EXPECTED_CERTIFICATION_TYPE = OOP_045_CERTIFICATION_TYPE
EXPECTED_FREEZE_RECORD_TYPE = OOP_045_FREEZE_RECORD_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorSubsystemCompletionReadinessInvariantError(RuntimeError):
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
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorSubsystemCompletionReadinessInvariantError(
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
class OracleOperatorSubsystemCompletionReadiness:
    oracle_operator_subsystem_completion_readiness_id: str
    source_presentation_subsystem_completion_certification_id: str
    source_presentation_subsystem_completion_certification_hash: str
    source_publication_completion_attestation_id: str
    source_publication_completion_attestation_hash: str
    source_publication_result_certification_id: str
    source_publication_result_certification_hash: str
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
    published_presentation_artifact_type: str
    published_presentation_format: str
    presentation_certification_type: str
    presentation_freeze_record_type: str
    readiness_type: str
    readiness_record_type: str
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    operator_session_id: str
    operator_session_payload_hash: str
    operator_console_id: str
    operator_console_payload_hash: str
    rendered_console_id: str
    rendered_console_payload_hash: str
    rendered_presentation_id: str
    rendered_presentation_payload_hash: str
    published_presentation_id: str
    published_presentation_payload_hash: str
    presentation_freeze_record_id: str
    presentation_freeze_record_payload_hash: str
    readiness_record_id: str
    readiness_record_payload: Mapping[str, Any]
    readiness_record_payload_hash: str
    presentation_certification_identity_verified: bool
    presentation_certification_hash_verified: bool
    presentation_certification_status_verified: bool
    presentation_certification_type_verified: bool
    presentation_freeze_record_type_verified: bool
    presentation_freeze_record_identity_verified: bool
    presentation_freeze_record_payload_hash_verified: bool
    operator_namespace_verified: bool
    presentation_namespace_verified: bool
    query_boundary_verified: bool
    research_response_boundary_verified: bool
    session_boundary_verified: bool
    console_boundary_verified: bool
    presentation_boundary_verified: bool
    publication_chain_completion_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    deterministic_readiness_verified: bool
    immutable_readiness_record_verified: bool
    read_only_operator_subsystem_verified: bool
    operator_presentation_subsystem_completion_certified: bool
    operator_presentation_subsystem_frozen: bool
    operator_query_boundary_complete: bool
    operator_research_response_boundary_complete: bool
    operator_session_boundary_complete: bool
    operator_console_boundary_complete: bool
    operator_presentation_boundary_complete: bool
    oracle_operator_subsystem_completion_ready: bool
    oracle_operator_subsystem_completion_certified: bool
    further_operator_builds_required: bool
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
    oracle_operator_subsystem_completion_readiness_hash: str


class OracleOperatorSubsystemCompletionReadinessGate:
    @staticmethod
    def _verify(
        certification: OracleOperatorPresentationSubsystemCompletionCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorPresentationSubsystemCompletionCertification,
        ):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "source must be canonical OOP-045 presentation completion certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop(
            "oracle_operator_presentation_subsystem_completion_certification_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 certification hash mismatch"
            )

        if certification.certification_status != EXPECTED_CERTIFICATION_STATUS:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 certification status mismatch"
            )
        if certification.certification_type != EXPECTED_CERTIFICATION_TYPE:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 certification type mismatch"
            )
        if certification.freeze_record_type != EXPECTED_FREEZE_RECORD_TYPE:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 freeze record type mismatch"
            )
        if certification.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "operator namespace mismatch"
            )
        if certification.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(certification.freeze_record_id):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze record id invalid"
            )
        if not _valid_sha256(certification.freeze_record_payload_hash):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze record payload hash invalid"
            )
        if stable_hash(certification.freeze_record_payload) != certification.freeze_record_payload_hash:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze record payload hash mismatch"
            )

        freeze_payload = certification.freeze_record_payload
        if freeze_payload.get("freeze_record_id") != certification.freeze_record_id:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze record identity mismatch"
            )
        if freeze_payload.get("presentation_namespace") != certification.presentation_namespace:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze namespace mismatch"
            )
        if freeze_payload.get("published_presentation_id") != certification.published_presentation_id:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "published presentation identity mismatch"
            )
        if freeze_payload.get("published_presentation_payload_hash") != certification.published_presentation_payload_hash:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "published presentation payload hash mismatch"
            )

        required_freeze_state = (
            freeze_payload.get("publication_chain_complete") is True,
            freeze_payload.get("presentation_subsystem_complete") is True,
            freeze_payload.get("presentation_subsystem_frozen") is True,
            freeze_payload.get("further_presentation_certification_required") is False,
            freeze_payload.get("read_only") is True,
            freeze_payload.get("qseries_handoff_disabled") is True,
            freeze_payload.get("qseries_execution_disabled") is True,
            freeze_payload.get("orders_disabled") is True,
            freeze_payload.get("funds_movement_disabled") is True,
            freeze_payload.get("portfolio_mutation_disabled") is True,
        )
        if not all(required_freeze_state):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze state mismatch"
            )

        required = (
            certification.attestation_identity_verified,
            certification.attestation_hash_verified,
            certification.attestation_status_verified,
            certification.attestation_type_verified,
            certification.completion_record_type_verified,
            certification.completion_record_identity_verified,
            certification.completion_record_payload_hash_verified,
            certification.published_presentation_identity_verified,
            certification.published_presentation_payload_hash_verified,
            certification.publication_chain_completion_verified,
            certification.complete_lineage_verified,
            certification.frozen_scope_verified,
            certification.frozen_scope_preserved,
            certification.deterministic_certification_verified,
            certification.immutable_freeze_record_verified,
            certification.read_only_subsystem_verified,
            certification.publication_result_certified,
            certification.publication_completion_attested,
            certification.presentation_publication_chain_complete,
            certification.operator_presentation_subsystem_completion_ready,
            certification.operator_presentation_subsystem_completion_certified,
            certification.operator_presentation_subsystem_frozen,
        )
        if not all(required):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 presentation completion certification incomplete"
            )
        if certification.further_presentation_certification_required:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation subsystem still requires certification"
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
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "forbidden downstream activity detected"
            )

    def evaluate(
        self,
        *,
        certification: OracleOperatorPresentationSubsystemCompletionCertification,
    ) -> OracleOperatorSubsystemCompletionReadiness:
        self._verify(certification)

        readiness_record_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_presentation_certification_id": certification.oracle_operator_presentation_subsystem_completion_certification_id,
                "source_presentation_certification_hash": certification.oracle_operator_presentation_subsystem_completion_certification_hash,
                "presentation_freeze_record_id": certification.freeze_record_id,
                "presentation_freeze_record_payload_hash": certification.freeze_record_payload_hash,
                "readiness_record_type": READINESS_RECORD_TYPE,
            }
        )

        readiness_record_payload = {
            "readiness_record_id": readiness_record_id,
            "readiness_record_type": READINESS_RECORD_TYPE,
            "operator_namespace": certification.operator_namespace,
            "query_namespace": certification.query_namespace,
            "research_response_namespace": certification.research_response_namespace,
            "session_namespace": certification.session_namespace,
            "console_namespace": certification.console_namespace,
            "presentation_namespace": certification.presentation_namespace,
            "presentation_subsystem_completion_certification_id": certification.oracle_operator_presentation_subsystem_completion_certification_id,
            "presentation_subsystem_completion_certification_hash": certification.oracle_operator_presentation_subsystem_completion_certification_hash,
            "presentation_freeze_record_id": certification.freeze_record_id,
            "presentation_freeze_record_payload_hash": certification.freeze_record_payload_hash,
            "published_presentation_id": certification.published_presentation_id,
            "published_presentation_payload_hash": certification.published_presentation_payload_hash,
            "query_boundary_complete": True,
            "research_response_boundary_complete": True,
            "session_boundary_complete": True,
            "console_boundary_complete": True,
            "presentation_boundary_complete": True,
            "operator_subsystem_completion_ready": True,
            "operator_subsystem_completion_certified": False,
            "further_operator_builds_required": True,
            "read_only": True,
            "qseries_handoff_disabled": True,
            "qseries_execution_disabled": True,
            "orders_disabled": True,
            "funds_movement_disabled": True,
            "portfolio_mutation_disabled": True,
        }
        readiness_record_payload_hash = stable_hash(readiness_record_payload)

        readiness_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "readiness_record_id": readiness_record_id,
                "readiness_record_payload_hash": readiness_record_payload_hash,
                "readiness_type": READINESS_TYPE,
            }
        )

        body = {
            "oracle_operator_subsystem_completion_readiness_id": readiness_id,
            "source_presentation_subsystem_completion_certification_id": certification.oracle_operator_presentation_subsystem_completion_certification_id,
            "source_presentation_subsystem_completion_certification_hash": certification.oracle_operator_presentation_subsystem_completion_certification_hash,
            "source_publication_completion_attestation_id": certification.source_publication_completion_attestation_id,
            "source_publication_completion_attestation_hash": certification.source_publication_completion_attestation_hash,
            "source_publication_result_certification_id": certification.source_publication_result_certification_id,
            "source_publication_result_certification_hash": certification.source_publication_result_certification_hash,
            "operator_namespace": certification.operator_namespace,
            "query_namespace": certification.query_namespace,
            "research_response_namespace": certification.research_response_namespace,
            "session_namespace": certification.session_namespace,
            "console_namespace": certification.console_namespace,
            "presentation_namespace": certification.presentation_namespace,
            "consumer_id": certification.consumer_id,
            "query_text": certification.query_text,
            "query_mode": certification.query_mode,
            "projection": certification.projection,
            "time_scope": certification.time_scope,
            "sort_order": certification.sort_order,
            "result_limit": certification.result_limit,
            "requested_tags": tuple(certification.requested_tags),
            "published_presentation_artifact_type": certification.published_presentation_artifact_type,
            "published_presentation_format": certification.published_presentation_format,
            "presentation_certification_type": certification.certification_type,
            "presentation_freeze_record_type": certification.freeze_record_type,
            "readiness_type": READINESS_TYPE,
            "readiness_record_type": READINESS_RECORD_TYPE,
            "research_response_id": certification.research_response_id,
            "research_response_payload_hash": certification.research_response_payload_hash,
            "research_response_item_count": certification.research_response_item_count,
            "operator_session_id": certification.operator_session_id,
            "operator_session_payload_hash": certification.operator_session_payload_hash,
            "operator_console_id": certification.operator_console_id,
            "operator_console_payload_hash": certification.operator_console_payload_hash,
            "rendered_console_id": certification.rendered_console_id,
            "rendered_console_payload_hash": certification.rendered_console_payload_hash,
            "rendered_presentation_id": certification.rendered_presentation_id,
            "rendered_presentation_payload_hash": certification.rendered_presentation_payload_hash,
            "published_presentation_id": certification.published_presentation_id,
            "published_presentation_payload_hash": certification.published_presentation_payload_hash,
            "presentation_freeze_record_id": certification.freeze_record_id,
            "presentation_freeze_record_payload_hash": certification.freeze_record_payload_hash,
            "readiness_record_id": readiness_record_id,
            "readiness_record_payload": readiness_record_payload,
            "readiness_record_payload_hash": readiness_record_payload_hash,
            "presentation_certification_identity_verified": True,
            "presentation_certification_hash_verified": True,
            "presentation_certification_status_verified": True,
            "presentation_certification_type_verified": True,
            "presentation_freeze_record_type_verified": True,
            "presentation_freeze_record_identity_verified": True,
            "presentation_freeze_record_payload_hash_verified": True,
            "operator_namespace_verified": True,
            "presentation_namespace_verified": True,
            "query_boundary_verified": True,
            "research_response_boundary_verified": True,
            "session_boundary_verified": True,
            "console_boundary_verified": True,
            "presentation_boundary_verified": True,
            "publication_chain_completion_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "deterministic_readiness_verified": True,
            "immutable_readiness_record_verified": True,
            "read_only_operator_subsystem_verified": True,
            "operator_presentation_subsystem_completion_certified": True,
            "operator_presentation_subsystem_frozen": True,
            "operator_query_boundary_complete": True,
            "operator_research_response_boundary_complete": True,
            "operator_session_boundary_complete": True,
            "operator_console_boundary_complete": True,
            "operator_presentation_boundary_complete": True,
            "oracle_operator_subsystem_completion_ready": True,
            "oracle_operator_subsystem_completion_certified": False,
            "further_operator_builds_required": True,
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

        return OracleOperatorSubsystemCompletionReadiness(
            **body,
            oracle_operator_subsystem_completion_readiness_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "READINESS_STATUS",
    "READINESS_TYPE",
    "READINESS_RECORD_TYPE",
    "OracleOperatorSubsystemCompletionReadiness",
    "OracleOperatorSubsystemCompletionReadinessGate",
    "OracleOperatorSubsystemCompletionReadinessInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_045_oracle_operator_presentation_subsystem_completion_certification_gate import (
    _attestation,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_subsystem_completion_certification_gate import (
    OracleOperatorPresentationSubsystemCompletionCertificationGate,
)
from qseries_v2.oracle_operator.oracle_operator_subsystem_completion_readiness_gate import (
    READINESS_RECORD_TYPE,
    READINESS_STATUS,
    READINESS_TYPE,
    OracleOperatorSubsystemCompletionReadinessGate,
    OracleOperatorSubsystemCompletionReadinessInvariantError,
    stable_hash,
)


def _presentation_certification():
    return OracleOperatorPresentationSubsystemCompletionCertificationGate().certify(
        attestation=_attestation()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe operator subsystem readiness accepted")
    except OracleOperatorSubsystemCompletionReadinessInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-046 TEST")
    print(" ORACLE OPERATOR SUBSYSTEM")
    print(" COMPLETION READINESS GATE")
    print("=" * 40)

    certification = _presentation_certification()
    gate = OracleOperatorSubsystemCompletionReadinessGate()

    first = gate.evaluate(certification=certification)
    repeated = gate.evaluate(certification=certification)

    assert first == repeated
    assert first.oracle_operator_subsystem_completion_readiness_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "oracle_operator_subsystem_completion_readiness_hash"
        }
    )
    assert first.readiness_record_payload_hash == stable_hash(first.readiness_record_payload)
    assert first.readiness_type == READINESS_TYPE
    assert first.readiness_record_type == READINESS_RECORD_TYPE
    assert first.readiness_status == READINESS_STATUS

    payload = first.readiness_record_payload
    assert payload["readiness_record_id"] == first.readiness_record_id
    assert payload["operator_namespace"] == first.operator_namespace
    assert payload["presentation_subsystem_completion_certification_id"] == first.source_presentation_subsystem_completion_certification_id
    assert payload["query_boundary_complete"] is True
    assert payload["research_response_boundary_complete"] is True
    assert payload["session_boundary_complete"] is True
    assert payload["console_boundary_complete"] is True
    assert payload["presentation_boundary_complete"] is True
    assert payload["operator_subsystem_completion_ready"] is True
    assert payload["operator_subsystem_completion_certified"] is False
    assert payload["further_operator_builds_required"] is True
    assert payload["read_only"] is True
    assert payload["qseries_handoff_disabled"] is True
    assert payload["qseries_execution_disabled"] is True
    assert payload["orders_disabled"] is True
    assert payload["funds_movement_disabled"] is True
    assert payload["portfolio_mutation_disabled"] is True

    assert first.presentation_certification_identity_verified
    assert first.presentation_certification_hash_verified
    assert first.presentation_certification_status_verified
    assert first.presentation_certification_type_verified
    assert first.presentation_freeze_record_type_verified
    assert first.presentation_freeze_record_identity_verified
    assert first.presentation_freeze_record_payload_hash_verified
    assert first.operator_namespace_verified
    assert first.presentation_namespace_verified
    assert first.query_boundary_verified
    assert first.research_response_boundary_verified
    assert first.session_boundary_verified
    assert first.console_boundary_verified
    assert first.presentation_boundary_verified
    assert first.publication_chain_completion_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.deterministic_readiness_verified
    assert first.immutable_readiness_record_verified
    assert first.read_only_operator_subsystem_verified

    assert first.operator_presentation_subsystem_completion_certified
    assert first.operator_presentation_subsystem_frozen
    assert first.operator_query_boundary_complete
    assert first.operator_research_response_boundary_complete
    assert first.operator_session_boundary_complete
    assert first.operator_console_boundary_complete
    assert first.operator_presentation_boundary_complete
    assert first.oracle_operator_subsystem_completion_ready
    assert not first.oracle_operator_subsystem_completion_certified
    assert first.further_operator_builds_required

    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed

    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        oracle_operator_presentation_subsystem_completion_certification_hash="0" * 64,
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        certification_status="wrong_status",
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        freeze_record_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        operator_presentation_subsystem_frozen=False,
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        further_presentation_certification_required=True,
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-045 Presentation subsystem certification consumed")
    print("[PASS] Presentation certification identity, hash, status, and type verified")
    print("[PASS] Presentation freeze record identity and payload hash verified")
    print("[PASS] Query, Research Response, Session, Console, and Presentation boundaries verified")
    print("[PASS] Complete Oracle Operator lineage preserved")
    print("[PASS] Immutable terminal subsystem readiness record created")
    print("[PASS] Oracle Operator subsystem marked completion-ready")
    print("[PASS] Final subsystem certification remains pending")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe readiness inputs rejected")
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
    print(" OOP-046 INSTALLER")
    print(" ORACLE OPERATOR SUBSYSTEM")
    print(" COMPLETION READINESS GATE")
    print("=" * 40)

    verify(
        SOURCE_045,
        "OOP-045",
        (
            'SCHEMA_VERSION = "OOP-045"',
            "class OracleOperatorPresentationSubsystemCompletionCertification",
            "oracle_operator_presentation_subsystem_completion_certification_hash",
            "freeze_record_payload_hash",
            "operator_presentation_subsystem_completion_certified",
            "operator_presentation_subsystem_frozen",
            "further_presentation_certification_required",
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
        SOURCE_045: sha256_file(SOURCE_045),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        OPERATOR_INIT,
        "from .oracle_operator_subsystem_completion_readiness_gate import *",
    )

    for path in (PRODUCTION, TEST, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-045 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics, Query, Research Response, Session, Console, or Presentation export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-046 test executed automatically")
    print()
    print("[DONE] OOP-046 Oracle Operator subsystem completion readiness installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
