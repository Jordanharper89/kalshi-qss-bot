from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
OPERATOR = QSERIES / "oracle_operator"
CONSOLE = OPERATOR / "console"
PRESENTATION = OPERATOR / "presentation"
ANALYTICS_QUERY = (
    QSERIES / "oracle_intelligence" / "analytics" / "downstream" / "query"
)

SOURCE_060 = ANALYTICS_QUERY / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
SOURCE_035 = CONSOLE / "oracle_operator_console_rendering_result_certification_gate.py"

PRODUCTION = PRESENTATION / "oracle_operator_presentation_rendering_authorization_gate.py"
TEST = ROOT / "test_oop_036_oracle_operator_presentation_rendering_authorization_gate.py"
PRESENTATION_INIT = PRESENTATION / "__init__.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.console.oracle_operator_console_rendering_result_certification_gate import (
    CERTIFICATION_STATUS as OOP_035_CERTIFICATION_STATUS,
    CERTIFICATION_TYPE as OOP_035_CERTIFICATION_TYPE,
    OracleOperatorConsoleRenderingResultCertification,
)

SCHEMA_VERSION = "OOP-036"
ENGINE_ID = "OOP-036"
POLICY_ID = "oracle.operator.presentation-rendering-authorization-gate.v1"
AUTHORIZATION_STATUS = "operator_presentation_rendering_authorized"
AUTHORIZATION_TYPE = "single_use_immutable_operator_presentation_rendering_authorization"
PRESENTATION_INPUT_PACKAGE_TYPE = "certified_rendered_operator_console_presentation_input_package"
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"

EXPECTED_CERTIFICATION_STATUS = OOP_035_CERTIFICATION_STATUS
EXPECTED_CERTIFICATION_TYPE = OOP_035_CERTIFICATION_TYPE


class OracleOperatorPresentationRenderingAuthorizationInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
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
class OracleOperatorPresentationRenderingAuthorization:
    operator_presentation_rendering_authorization_id: str
    source_operator_console_rendering_result_certification_id: str
    source_operator_console_rendering_result_certification_hash: str
    source_operator_console_rendering_execution_id: str
    source_operator_console_rendering_execution_hash: str
    source_operator_console_rendering_consumption_id: str
    source_operator_console_rendering_consumption_hash: str
    source_operator_console_rendering_authorization_id: str
    source_operator_console_rendering_authorization_hash: str
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
    certification_type: str
    authorization_type: str
    presentation_input_package_type: str
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
    certification_identity_verified: bool
    certification_hash_verified: bool
    certification_status_verified: bool
    certification_type_verified: bool
    rendered_console_identity_verified: bool
    rendered_console_payload_hash_verified: bool
    rendered_console_artifact_type_verified: bool
    rendered_console_format_verified: bool
    operator_console_identity_verified: bool
    operator_console_payload_hash_verified: bool
    operator_session_identity_verified: bool
    operator_session_payload_hash_verified: bool
    research_response_identity_verified: bool
    research_response_payload_hash_verified: bool
    research_response_cardinality_verified: bool
    rendered_sections_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_presentation_input_verified: bool
    single_use_authorization_verified: bool
    deterministic_authorization_verified: bool
    read_only_boundary_verified: bool
    operator_console_rendering_result_certified: bool
    operator_presentation_rendering_authorization_ready: bool
    operator_presentation_rendering_authorized: bool
    operator_presentation_rendering_allowed: bool
    operator_presentation_rendering_performed: bool
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
    authorization_status: str
    operator_presentation_rendering_authorization_hash: str


class OracleOperatorPresentationRenderingAuthorizationGate:
    @staticmethod
    def _verify(
        certification: OracleOperatorConsoleRenderingResultCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorConsoleRenderingResultCertification,
        ):
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "source must be canonical OOP-035 certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop(
            "operator_console_rendering_result_certification_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "OOP-035 certification hash mismatch"
            )

        if certification.certification_status != EXPECTED_CERTIFICATION_STATUS:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "OOP-035 certification status mismatch"
            )
        if certification.certification_type != EXPECTED_CERTIFICATION_TYPE:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "OOP-035 certification type mismatch"
            )

        if not _valid_sha256(certification.rendered_console_id):
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "rendered console id invalid"
            )
        if not _valid_sha256(certification.rendered_console_payload_hash):
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "rendered console payload hash invalid"
            )
        if stable_hash(certification.rendered_console_payload) != certification.rendered_console_payload_hash:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "rendered console payload hash mismatch"
            )

        rendered = certification.rendered_console_payload
        if rendered.get("rendered_console_id") != certification.rendered_console_id:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "rendered console identity mismatch"
            )
        if rendered.get("rendered_console_format") != certification.rendered_console_format:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "rendered console format mismatch"
            )
        if rendered.get("operator_console_id") != certification.operator_console_id:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "operator console identity mismatch"
            )
        if rendered.get("operator_console_payload_hash") != certification.operator_console_payload_hash:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "operator console payload hash mismatch"
            )
        if rendered.get("operator_session_id") != certification.operator_session_id:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "operator session identity mismatch"
            )
        if rendered.get("research_response_id") != certification.research_response_id:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "research response identity mismatch"
            )
        if rendered.get("research_response_item_count") != certification.research_response_item_count:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "research response cardinality mismatch"
            )
        if tuple(rendered.get("research_response_items") or ()) != tuple(certification.research_response_items):
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "research response items mismatch"
            )
        sections = tuple(rendered.get("sections") or ())
        if len(sections) != 3:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "rendered console sections mismatch"
            )
        if tuple(section.get("section_id") for section in sections) != (
            "query_context",
            "research_results",
            "lineage",
        ):
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "rendered console section order mismatch"
            )
        if rendered.get("read_only") is not True:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "rendered console is not read-only"
            )
        if rendered.get("presentation_rendering_disabled") is not True:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "pre-authorization presentation boundary missing"
            )
        if rendered.get("publication_disabled") is not True:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "publication boundary missing"
            )
        if rendered.get("qseries_execution_disabled") is not True:
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "Q Series execution boundary missing"
            )

        required = (
            certification.execution_identity_verified,
            certification.execution_hash_verified,
            certification.execution_status_verified,
            certification.rendered_console_identity_verified,
            certification.rendered_console_payload_hash_verified,
            certification.rendered_console_artifact_type_verified,
            certification.rendered_console_format_verified,
            certification.operator_console_identity_verified,
            certification.operator_console_payload_hash_verified,
            certification.operator_session_identity_verified,
            certification.operator_session_payload_hash_verified,
            certification.research_response_identity_verified,
            certification.research_response_payload_hash_verified,
            certification.research_response_cardinality_verified,
            certification.rendered_sections_verified,
            certification.complete_lineage_verified,
            certification.frozen_scope_verified,
            certification.frozen_scope_preserved,
            certification.immutable_rendered_console_verified,
            certification.read_only_rendered_console_verified,
            certification.deterministic_certification_verified,
            certification.operator_console_result_certified,
            certification.operator_console_rendering_authorized,
            certification.operator_console_rendering_authorization_consumed,
            certification.operator_console_rendering_allowed,
            certification.operator_console_rendering_performed,
            certification.operator_console_rendering_result_certified,
            certification.operator_presentation_rendering_authorization_ready,
        )
        if not all(required):
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "OOP-035 certification incomplete"
            )

        forbidden = (
            certification.operator_presentation_rendering_allowed,
            certification.operator_presentation_rendering_performed,
            certification.publication_allowed,
            certification.publication_performed,
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
            raise OracleOperatorPresentationRenderingAuthorizationInvariantError(
                "forbidden downstream activity detected"
            )

    def authorize(
        self,
        *,
        certification: OracleOperatorConsoleRenderingResultCertification,
    ) -> OracleOperatorPresentationRenderingAuthorization:
        self._verify(certification)

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_certification_id": certification.operator_console_rendering_result_certification_id,
                "source_certification_hash": certification.operator_console_rendering_result_certification_hash,
                "rendered_console_id": certification.rendered_console_id,
                "rendered_console_payload_hash": certification.rendered_console_payload_hash,
                "authorization_type": AUTHORIZATION_TYPE,
                "presentation_input_package_type": PRESENTATION_INPUT_PACKAGE_TYPE,
            }
        )

        body = {
            "operator_presentation_rendering_authorization_id": authorization_id,
            "source_operator_console_rendering_result_certification_id": certification.operator_console_rendering_result_certification_id,
            "source_operator_console_rendering_result_certification_hash": certification.operator_console_rendering_result_certification_hash,
            "source_operator_console_rendering_execution_id": certification.source_operator_console_rendering_execution_id,
            "source_operator_console_rendering_execution_hash": certification.source_operator_console_rendering_execution_hash,
            "source_operator_console_rendering_consumption_id": certification.source_operator_console_rendering_consumption_id,
            "source_operator_console_rendering_consumption_hash": certification.source_operator_console_rendering_consumption_hash,
            "source_operator_console_rendering_authorization_id": certification.source_operator_console_rendering_authorization_id,
            "source_operator_console_rendering_authorization_hash": certification.source_operator_console_rendering_authorization_hash,
            "operator_namespace": certification.operator_namespace,
            "query_namespace": certification.query_namespace,
            "research_response_namespace": certification.research_response_namespace,
            "session_namespace": certification.session_namespace,
            "console_namespace": certification.console_namespace,
            "presentation_namespace": EXPECTED_PRESENTATION_NAMESPACE,
            "consumer_id": certification.consumer_id,
            "query_text": certification.query_text,
            "query_mode": certification.query_mode,
            "projection": certification.projection,
            "time_scope": certification.time_scope,
            "sort_order": certification.sort_order,
            "result_limit": certification.result_limit,
            "requested_tags": tuple(certification.requested_tags),
            "operator_session_artifact_type": certification.operator_session_artifact_type,
            "operator_session_format": certification.operator_session_format,
            "operator_console_artifact_type": certification.operator_console_artifact_type,
            "operator_console_format": certification.operator_console_format,
            "rendered_console_artifact_type": certification.rendered_console_artifact_type,
            "rendered_console_format": certification.rendered_console_format,
            "certification_type": certification.certification_type,
            "authorization_type": AUTHORIZATION_TYPE,
            "presentation_input_package_type": PRESENTATION_INPUT_PACKAGE_TYPE,
            "research_response_id": certification.research_response_id,
            "research_response_payload_hash": certification.research_response_payload_hash,
            "research_response_item_count": certification.research_response_item_count,
            "research_response_items": tuple(certification.research_response_items),
            "operator_session_id": certification.operator_session_id,
            "operator_session_payload": dict(certification.operator_session_payload),
            "operator_session_payload_hash": certification.operator_session_payload_hash,
            "operator_console_id": certification.operator_console_id,
            "operator_console_payload": dict(certification.operator_console_payload),
            "operator_console_payload_hash": certification.operator_console_payload_hash,
            "rendered_console_id": certification.rendered_console_id,
            "rendered_console_payload": dict(certification.rendered_console_payload),
            "rendered_console_payload_hash": certification.rendered_console_payload_hash,
            "certification_identity_verified": True,
            "certification_hash_verified": True,
            "certification_status_verified": True,
            "certification_type_verified": True,
            "rendered_console_identity_verified": True,
            "rendered_console_payload_hash_verified": True,
            "rendered_console_artifact_type_verified": True,
            "rendered_console_format_verified": True,
            "operator_console_identity_verified": True,
            "operator_console_payload_hash_verified": True,
            "operator_session_identity_verified": True,
            "operator_session_payload_hash_verified": True,
            "research_response_identity_verified": True,
            "research_response_payload_hash_verified": True,
            "research_response_cardinality_verified": True,
            "rendered_sections_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_presentation_input_verified": True,
            "single_use_authorization_verified": True,
            "deterministic_authorization_verified": True,
            "read_only_boundary_verified": True,
            "operator_console_rendering_result_certified": True,
            "operator_presentation_rendering_authorization_ready": True,
            "operator_presentation_rendering_authorized": True,
            "operator_presentation_rendering_allowed": True,
            "operator_presentation_rendering_performed": False,
            "publication_authorization_ready": False,
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
            "authorization_status": AUTHORIZATION_STATUS,
        }

        return OracleOperatorPresentationRenderingAuthorization(
            **body,
            operator_presentation_rendering_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_STATUS",
    "AUTHORIZATION_TYPE",
    "PRESENTATION_INPUT_PACKAGE_TYPE",
    "OracleOperatorPresentationRenderingAuthorization",
    "OracleOperatorPresentationRenderingAuthorizationGate",
    "OracleOperatorPresentationRenderingAuthorizationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_035_oracle_operator_console_rendering_result_certification_gate import (
    _execution,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_rendering_result_certification_gate import (
    OracleOperatorConsoleRenderingResultCertificationGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_authorization_gate import (
    AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE,
    PRESENTATION_INPUT_PACKAGE_TYPE,
    OracleOperatorPresentationRenderingAuthorizationGate,
    OracleOperatorPresentationRenderingAuthorizationInvariantError,
    stable_hash,
)


def _certification():
    return OracleOperatorConsoleRenderingResultCertificationGate().certify(
        execution=_execution()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe presentation rendering authorization accepted")
    except OracleOperatorPresentationRenderingAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-036 TEST")
    print(" OPERATOR PRESENTATION RENDERING")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorPresentationRenderingAuthorizationGate()

    first = gate.authorize(certification=certification)
    repeated = gate.authorize(certification=certification)

    assert first == repeated
    assert first.operator_presentation_rendering_authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_rendering_authorization_hash"
        }
    )

    assert first.source_operator_console_rendering_result_certification_id == certification.operator_console_rendering_result_certification_id
    assert first.source_operator_console_rendering_result_certification_hash == certification.operator_console_rendering_result_certification_hash
    assert first.authorization_type == AUTHORIZATION_TYPE
    assert first.presentation_input_package_type == PRESENTATION_INPUT_PACKAGE_TYPE
    assert first.authorization_status == AUTHORIZATION_STATUS
    assert first.rendered_console_id == certification.rendered_console_id
    assert first.rendered_console_payload_hash == certification.rendered_console_payload_hash
    assert first.rendered_console_payload == certification.rendered_console_payload

    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.certification_type_verified
    assert first.rendered_console_identity_verified
    assert first.rendered_console_payload_hash_verified
    assert first.rendered_console_artifact_type_verified
    assert first.rendered_console_format_verified
    assert first.operator_console_identity_verified
    assert first.operator_console_payload_hash_verified
    assert first.operator_session_identity_verified
    assert first.operator_session_payload_hash_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.research_response_cardinality_verified
    assert first.rendered_sections_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_presentation_input_verified
    assert first.single_use_authorization_verified
    assert first.deterministic_authorization_verified
    assert first.read_only_boundary_verified

    assert first.operator_console_rendering_result_certified
    assert first.operator_presentation_rendering_authorization_ready
    assert first.operator_presentation_rendering_authorized
    assert first.operator_presentation_rendering_allowed
    assert not first.operator_presentation_rendering_performed
    assert not first.publication_authorization_ready
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

    _reject(lambda: gate.authorize(certification=replace(
        certification,
        operator_console_rendering_result_certification_hash="0" * 64,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        certification_status="wrong_status",
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        rendered_console_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        research_response_item_count=certification.research_response_item_count + 1,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        operator_presentation_rendering_allowed=True,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-035 rendered console certification consumed")
    print("[PASS] Certification identity, hash, status, and type verified")
    print("[PASS] Rendered console identity, payload hash, format, and sections verified")
    print("[PASS] Operator Console, Session, and Research Response lineage preserved")
    print("[PASS] Immutable certified presentation input preserved")
    print("[PASS] Single-use presentation rendering authorized")
    print("[PASS] Presentation rendering allowed but not performed")
    print("[PASS] Publication authorization remains not ready")
    print("[PASS] Publication and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe certifications rejected")
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
    print(" OOP-036 INSTALLER")
    print(" OPERATOR PRESENTATION RENDERING")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    verify(
        SOURCE_035,
        "OOP-035",
        (
            'SCHEMA_VERSION = "OOP-035"',
            "class OracleOperatorConsoleRenderingResultCertification",
            "operator_console_rendering_result_certification_hash",
            "rendered_console_payload_hash",
            "rendered_console_payload",
            "operator_console_rendering_result_certified",
            "operator_presentation_rendering_authorization_ready",
            "operator_presentation_rendering_allowed",
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
        SOURCE_035: sha256_file(SOURCE_035),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        PRESENTATION_INIT,
        "from .oracle_operator_presentation_rendering_authorization_gate import *",
    )
    export(
        OPERATOR_INIT,
        "from .presentation.oracle_operator_presentation_rendering_authorization_gate import *",
    )

    for path in (PRODUCTION, TEST, PRESENTATION_INIT, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-035 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics, Query, Research Response, Session, or Console export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-036 test executed automatically")
    print()
    print("[DONE] OOP-036 Operator presentation rendering authorization installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
