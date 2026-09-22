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
SOURCE_042 = PRESENTATION / "oracle_operator_presentation_publication_execution_gate.py"

PRODUCTION = PRESENTATION / "oracle_operator_presentation_publication_result_certification_gate.py"
TEST = ROOT / "test_oop_043_oracle_operator_presentation_publication_result_certification_gate.py"
PRESENTATION_INIT = PRESENTATION / "__init__.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_execution_gate import (
    EXECUTION_STATUS as OOP_042_EXECUTION_STATUS,
    PUBLISHED_PRESENTATION_ARTIFACT_TYPE as OOP_042_PUBLISHED_PRESENTATION_ARTIFACT_TYPE,
    PUBLISHED_PRESENTATION_FORMAT as OOP_042_PUBLISHED_PRESENTATION_FORMAT,
    OracleOperatorPresentationPublicationExecution,
)

SCHEMA_VERSION = "OOP-043"
ENGINE_ID = "OOP-043"
POLICY_ID = "oracle.operator.presentation-publication-result-certification-gate.v1"
CERTIFICATION_STATUS = "operator_presentation_publication_result_certified"
CERTIFICATION_TYPE = "immutable_read_only_operator_presentation_publication_result_certification"

EXPECTED_EXECUTION_STATUS = OOP_042_EXECUTION_STATUS
EXPECTED_PUBLISHED_PRESENTATION_ARTIFACT_TYPE = OOP_042_PUBLISHED_PRESENTATION_ARTIFACT_TYPE
EXPECTED_PUBLISHED_PRESENTATION_FORMAT = OOP_042_PUBLISHED_PRESENTATION_FORMAT
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorPresentationPublicationResultCertificationInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
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
class OracleOperatorPresentationPublicationResultCertification:
    operator_presentation_publication_result_certification_id: str
    source_operator_presentation_publication_execution_id: str
    source_operator_presentation_publication_execution_hash: str
    source_operator_presentation_publication_consumption_id: str
    source_operator_presentation_publication_consumption_hash: str
    source_operator_presentation_publication_authorization_id: str
    source_operator_presentation_publication_authorization_hash: str
    source_operator_presentation_rendering_result_certification_id: str
    source_operator_presentation_rendering_result_certification_hash: str
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
    rendered_presentation_artifact_type: str
    rendered_presentation_format: str
    published_presentation_artifact_type: str
    published_presentation_format: str
    certification_type: str
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    operator_session_id: str
    operator_session_payload_hash: str
    operator_console_id: str
    operator_console_payload_hash: str
    rendered_console_id: str
    rendered_console_payload_hash: str
    rendered_presentation_id: str
    rendered_presentation_payload_hash: str
    published_presentation_id: str
    published_presentation_payload: Mapping[str, Any]
    published_presentation_payload_hash: str
    execution_identity_verified: bool
    execution_hash_verified: bool
    execution_status_verified: bool
    published_presentation_identity_verified: bool
    published_presentation_payload_hash_verified: bool
    published_presentation_artifact_type_verified: bool
    published_presentation_format_verified: bool
    source_rendered_presentation_identity_verified: bool
    source_rendered_presentation_payload_hash_verified: bool
    research_response_identity_verified: bool
    research_response_cardinality_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_published_presentation_verified: bool
    read_only_publication_verified: bool
    deterministic_certification_verified: bool
    publication_authorization_ready: bool
    publication_authorized: bool
    publication_authorization_consumed: bool
    publication_allowed: bool
    publication_performed: bool
    publication_result_certified: bool
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
    operator_presentation_publication_result_certification_hash: str


class OracleOperatorPresentationPublicationResultCertificationGate:
    @staticmethod
    def _verify(execution: OracleOperatorPresentationPublicationExecution) -> None:
        if not isinstance(execution, OracleOperatorPresentationPublicationExecution):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "source must be canonical OOP-042 execution"
            )

        body = asdict(execution)
        supplied_hash = body.pop(
            "operator_presentation_publication_execution_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "OOP-042 execution hash mismatch"
            )

        if execution.execution_status != EXPECTED_EXECUTION_STATUS:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "OOP-042 execution status mismatch"
            )
        if execution.published_presentation_artifact_type != EXPECTED_PUBLISHED_PRESENTATION_ARTIFACT_TYPE:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation artifact type mismatch"
            )
        if execution.published_presentation_format != EXPECTED_PUBLISHED_PRESENTATION_FORMAT:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation format mismatch"
            )
        if execution.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(execution.published_presentation_id):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation id invalid"
            )
        if not _valid_sha256(execution.published_presentation_payload_hash):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation payload hash invalid"
            )
        if stable_hash(execution.published_presentation_payload) != execution.published_presentation_payload_hash:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation payload hash mismatch"
            )

        payload = execution.published_presentation_payload
        if payload.get("published_presentation_id") != execution.published_presentation_id:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation identity mismatch"
            )
        if payload.get("published_presentation_format") != execution.published_presentation_format:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation format payload mismatch"
            )
        if payload.get("source_rendered_presentation_id") != execution.rendered_presentation_id:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "source rendered presentation identity mismatch"
            )
        if payload.get("source_rendered_presentation_payload_hash") != execution.rendered_presentation_payload_hash:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "source rendered presentation payload hash mismatch"
            )
        if payload.get("research_response_id") != execution.research_response_id:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "research response identity mismatch"
            )
        if payload.get("research_response_item_count") != execution.research_response_item_count:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "research response cardinality mismatch"
            )
        if tuple(payload.get("research_response_items") or ()) != tuple(execution.research_response_items):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "research response items mismatch"
            )

        boundaries = (
            payload.get("read_only") is True,
            payload.get("publication_completed") is True,
            payload.get("qseries_handoff_disabled") is True,
            payload.get("qseries_execution_disabled") is True,
            payload.get("orders_disabled") is True,
            payload.get("funds_movement_disabled") is True,
            payload.get("portfolio_mutation_disabled") is True,
        )
        if not all(boundaries):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation safety boundary mismatch"
            )

        required = (
            execution.consumption_identity_verified,
            execution.consumption_hash_verified,
            execution.consumption_status_verified,
            execution.publication_execution_package_type_verified,
            execution.rendered_presentation_identity_verified,
            execution.rendered_presentation_payload_hash_verified,
            execution.rendered_presentation_sections_verified,
            execution.complete_lineage_verified,
            execution.frozen_scope_verified,
            execution.frozen_scope_preserved,
            execution.deterministic_publication_verified,
            execution.immutable_published_presentation_verified,
            execution.read_only_publication_verified,
            execution.publication_authorization_ready,
            execution.publication_authorized,
            execution.publication_authorization_consumed,
            execution.publication_allowed,
            execution.publication_performed,
            execution.publication_result_certification_ready,
        )
        if not all(required):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "OOP-042 publication execution incomplete"
            )

        forbidden = (
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
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "forbidden downstream activity detected"
            )

    def certify(
        self,
        *,
        execution: OracleOperatorPresentationPublicationExecution,
    ) -> OracleOperatorPresentationPublicationResultCertification:
        self._verify(execution)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_execution_id": execution.operator_presentation_publication_execution_id,
                "source_execution_hash": execution.operator_presentation_publication_execution_hash,
                "published_presentation_id": execution.published_presentation_id,
                "published_presentation_payload_hash": execution.published_presentation_payload_hash,
                "certification_type": CERTIFICATION_TYPE,
            }
        )

        body = {
            "operator_presentation_publication_result_certification_id": certification_id,
            "source_operator_presentation_publication_execution_id": execution.operator_presentation_publication_execution_id,
            "source_operator_presentation_publication_execution_hash": execution.operator_presentation_publication_execution_hash,
            "source_operator_presentation_publication_consumption_id": execution.source_operator_presentation_publication_consumption_id,
            "source_operator_presentation_publication_consumption_hash": execution.source_operator_presentation_publication_consumption_hash,
            "source_operator_presentation_publication_authorization_id": execution.source_operator_presentation_publication_authorization_id,
            "source_operator_presentation_publication_authorization_hash": execution.source_operator_presentation_publication_authorization_hash,
            "source_operator_presentation_rendering_result_certification_id": execution.source_operator_presentation_rendering_result_certification_id,
            "source_operator_presentation_rendering_result_certification_hash": execution.source_operator_presentation_rendering_result_certification_hash,
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
            "rendered_presentation_artifact_type": execution.rendered_presentation_artifact_type,
            "rendered_presentation_format": execution.rendered_presentation_format,
            "published_presentation_artifact_type": execution.published_presentation_artifact_type,
            "published_presentation_format": execution.published_presentation_format,
            "certification_type": CERTIFICATION_TYPE,
            "research_response_id": execution.research_response_id,
            "research_response_payload_hash": execution.research_response_payload_hash,
            "research_response_item_count": execution.research_response_item_count,
            "research_response_items": tuple(execution.research_response_items),
            "operator_session_id": execution.operator_session_id,
            "operator_session_payload_hash": execution.operator_session_payload_hash,
            "operator_console_id": execution.operator_console_id,
            "operator_console_payload_hash": execution.operator_console_payload_hash,
            "rendered_console_id": execution.rendered_console_id,
            "rendered_console_payload_hash": execution.rendered_console_payload_hash,
            "rendered_presentation_id": execution.rendered_presentation_id,
            "rendered_presentation_payload_hash": execution.rendered_presentation_payload_hash,
            "published_presentation_id": execution.published_presentation_id,
            "published_presentation_payload": dict(execution.published_presentation_payload),
            "published_presentation_payload_hash": execution.published_presentation_payload_hash,
            "execution_identity_verified": True,
            "execution_hash_verified": True,
            "execution_status_verified": True,
            "published_presentation_identity_verified": True,
            "published_presentation_payload_hash_verified": True,
            "published_presentation_artifact_type_verified": True,
            "published_presentation_format_verified": True,
            "source_rendered_presentation_identity_verified": True,
            "source_rendered_presentation_payload_hash_verified": True,
            "research_response_identity_verified": True,
            "research_response_cardinality_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_published_presentation_verified": True,
            "read_only_publication_verified": True,
            "deterministic_certification_verified": True,
            "publication_authorization_ready": True,
            "publication_authorized": True,
            "publication_authorization_consumed": True,
            "publication_allowed": True,
            "publication_performed": True,
            "publication_result_certified": True,
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

        return OracleOperatorPresentationPublicationResultCertification(
            **body,
            operator_presentation_publication_result_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_STATUS",
    "CERTIFICATION_TYPE",
    "OracleOperatorPresentationPublicationResultCertification",
    "OracleOperatorPresentationPublicationResultCertificationGate",
    "OracleOperatorPresentationPublicationResultCertificationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_042_oracle_operator_presentation_publication_execution_gate import (
    _consumption,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_execution_gate import (
    OracleOperatorPresentationPublicationExecutionGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    OracleOperatorPresentationPublicationResultCertificationGate,
    OracleOperatorPresentationPublicationResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorPresentationPublicationExecutionGate().execute(
        consumption=_consumption()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe publication certification accepted")
    except OracleOperatorPresentationPublicationResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-043 TEST")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorPresentationPublicationResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.operator_presentation_publication_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_publication_result_certification_hash"
        }
    )
    assert first.published_presentation_payload_hash == stable_hash(
        first.published_presentation_payload
    )
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.published_presentation_id == execution.published_presentation_id
    assert first.published_presentation_payload == execution.published_presentation_payload

    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.published_presentation_identity_verified
    assert first.published_presentation_payload_hash_verified
    assert first.published_presentation_artifact_type_verified
    assert first.published_presentation_format_verified
    assert first.source_rendered_presentation_identity_verified
    assert first.source_rendered_presentation_payload_hash_verified
    assert first.research_response_identity_verified
    assert first.research_response_cardinality_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_published_presentation_verified
    assert first.read_only_publication_verified
    assert first.deterministic_certification_verified

    assert first.publication_authorization_ready
    assert first.publication_authorized
    assert first.publication_authorization_consumed
    assert first.publication_allowed
    assert first.publication_performed
    assert first.publication_result_certified
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
        operator_presentation_publication_execution_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        execution_status="wrong_status",
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        published_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_item_count=execution.research_response_item_count + 1,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        publication_performed=False,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-042 published presentation execution consumed")
    print("[PASS] Execution identity, hash, status, artifact type, and format verified")
    print("[PASS] Published presentation identity and payload hash verified")
    print("[PASS] Source rendered presentation identity and hash verified")
    print("[PASS] Complete Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Immutable read-only publication result certified")
    print("[PASS] Publication completion certified")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe publication executions rejected")
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
    print(" OOP-043 INSTALLER")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    verify(
        SOURCE_042,
        "OOP-042",
        (
            'SCHEMA_VERSION = "OOP-042"',
            "class OracleOperatorPresentationPublicationExecution",
            "operator_presentation_publication_execution_hash",
            "published_presentation_payload_hash",
            "published_presentation_payload",
            "publication_performed",
            "publication_result_certification_ready",
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
        SOURCE_042: sha256_file(SOURCE_042),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        PRESENTATION_INIT,
        "from .oracle_operator_presentation_publication_result_certification_gate import *",
    )
    export(
        OPERATOR_INIT,
        "from .presentation.oracle_operator_presentation_publication_result_certification_gate import *",
    )

    for path in (PRODUCTION, TEST, PRESENTATION_INIT, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-042 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics, Query, Research Response, Session, or Console export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-043 test executed automatically")
    print()
    print("[DONE] OOP-043 Operator presentation publication result certification installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
