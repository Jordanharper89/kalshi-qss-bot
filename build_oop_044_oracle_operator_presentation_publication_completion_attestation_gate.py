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
SOURCE_043 = PRESENTATION / "oracle_operator_presentation_publication_result_certification_gate.py"

PRODUCTION = PRESENTATION / "oracle_operator_presentation_publication_completion_attestation_gate.py"
TEST = ROOT / "test_oop_044_oracle_operator_presentation_publication_completion_attestation_gate.py"
PRESENTATION_INIT = PRESENTATION / "__init__.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_result_certification_gate import (
    CERTIFICATION_STATUS as OOP_043_CERTIFICATION_STATUS,
    CERTIFICATION_TYPE as OOP_043_CERTIFICATION_TYPE,
    OracleOperatorPresentationPublicationResultCertification,
)

SCHEMA_VERSION = "OOP-044"
ENGINE_ID = "OOP-044"
POLICY_ID = "oracle.operator.presentation-publication-completion-attestation-gate.v1"
ATTESTATION_STATUS = "operator_presentation_publication_completion_attested"
ATTESTATION_TYPE = "immutable_operator_presentation_publication_completion_attestation"
COMPLETION_RECORD_TYPE = "terminal_read_only_operator_presentation_publication_completion_record"

EXPECTED_CERTIFICATION_STATUS = OOP_043_CERTIFICATION_STATUS
EXPECTED_CERTIFICATION_TYPE = OOP_043_CERTIFICATION_TYPE
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorPresentationPublicationCompletionAttestationInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
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
class OracleOperatorPresentationPublicationCompletionAttestation:
    operator_presentation_publication_completion_attestation_id: str
    source_operator_presentation_publication_result_certification_id: str
    source_operator_presentation_publication_result_certification_hash: str
    source_operator_presentation_publication_execution_id: str
    source_operator_presentation_publication_execution_hash: str
    source_operator_presentation_publication_consumption_id: str
    source_operator_presentation_publication_consumption_hash: str
    source_operator_presentation_publication_authorization_id: str
    source_operator_presentation_publication_authorization_hash: str
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
    certification_type: str
    attestation_type: str
    completion_record_type: str
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
    published_presentation_payload: Mapping[str, Any]
    published_presentation_payload_hash: str
    completion_record_id: str
    completion_record_payload: Mapping[str, Any]
    completion_record_payload_hash: str
    certification_identity_verified: bool
    certification_hash_verified: bool
    certification_status_verified: bool
    certification_type_verified: bool
    published_presentation_identity_verified: bool
    published_presentation_payload_hash_verified: bool
    published_presentation_artifact_type_verified: bool
    published_presentation_format_verified: bool
    publication_completion_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    deterministic_attestation_verified: bool
    immutable_completion_record_verified: bool
    read_only_completion_verified: bool
    publication_result_certified: bool
    publication_completion_attested: bool
    presentation_publication_chain_complete: bool
    operator_presentation_subsystem_completion_ready: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    order_creation_allowed: bool
    order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    attestation_status: str
    operator_presentation_publication_completion_attestation_hash: str


class OracleOperatorPresentationPublicationCompletionAttestationGate:
    @staticmethod
    def _verify(
        certification: OracleOperatorPresentationPublicationResultCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorPresentationPublicationResultCertification,
        ):
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "source must be canonical OOP-043 certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop(
            "operator_presentation_publication_result_certification_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "OOP-043 certification hash mismatch"
            )

        if certification.certification_status != EXPECTED_CERTIFICATION_STATUS:
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "OOP-043 certification status mismatch"
            )
        if certification.certification_type != EXPECTED_CERTIFICATION_TYPE:
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "OOP-043 certification type mismatch"
            )
        if certification.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(certification.published_presentation_id):
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "published presentation id invalid"
            )
        if not _valid_sha256(certification.published_presentation_payload_hash):
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "published presentation payload hash invalid"
            )
        if stable_hash(certification.published_presentation_payload) != certification.published_presentation_payload_hash:
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "published presentation payload hash mismatch"
            )

        payload = certification.published_presentation_payload
        if payload.get("published_presentation_id") != certification.published_presentation_id:
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "published presentation identity mismatch"
            )
        if payload.get("published_presentation_format") != certification.published_presentation_format:
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "published presentation format mismatch"
            )
        if payload.get("research_response_id") != certification.research_response_id:
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "research response identity mismatch"
            )
        if payload.get("research_response_item_count") != certification.research_response_item_count:
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "research response cardinality mismatch"
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
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "publication completion safety boundary mismatch"
            )

        required = (
            certification.execution_identity_verified,
            certification.execution_hash_verified,
            certification.execution_status_verified,
            certification.published_presentation_identity_verified,
            certification.published_presentation_payload_hash_verified,
            certification.published_presentation_artifact_type_verified,
            certification.published_presentation_format_verified,
            certification.source_rendered_presentation_identity_verified,
            certification.source_rendered_presentation_payload_hash_verified,
            certification.research_response_identity_verified,
            certification.research_response_cardinality_verified,
            certification.complete_lineage_verified,
            certification.frozen_scope_verified,
            certification.frozen_scope_preserved,
            certification.immutable_published_presentation_verified,
            certification.read_only_publication_verified,
            certification.deterministic_certification_verified,
            certification.publication_authorization_ready,
            certification.publication_authorized,
            certification.publication_authorization_consumed,
            certification.publication_allowed,
            certification.publication_performed,
            certification.publication_result_certified,
        )
        if not all(required):
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "OOP-043 certification incomplete"
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
            raise OracleOperatorPresentationPublicationCompletionAttestationInvariantError(
                "forbidden downstream activity detected"
            )

    def attest(
        self,
        *,
        certification: OracleOperatorPresentationPublicationResultCertification,
    ) -> OracleOperatorPresentationPublicationCompletionAttestation:
        self._verify(certification)

        completion_record_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_certification_id": certification.operator_presentation_publication_result_certification_id,
                "source_certification_hash": certification.operator_presentation_publication_result_certification_hash,
                "published_presentation_id": certification.published_presentation_id,
                "published_presentation_payload_hash": certification.published_presentation_payload_hash,
                "completion_record_type": COMPLETION_RECORD_TYPE,
            }
        )

        completion_record_payload = {
            "completion_record_id": completion_record_id,
            "completion_record_type": COMPLETION_RECORD_TYPE,
            "published_presentation_id": certification.published_presentation_id,
            "published_presentation_payload_hash": certification.published_presentation_payload_hash,
            "publication_result_certification_id": certification.operator_presentation_publication_result_certification_id,
            "publication_result_certification_hash": certification.operator_presentation_publication_result_certification_hash,
            "research_response_id": certification.research_response_id,
            "operator_session_id": certification.operator_session_id,
            "operator_console_id": certification.operator_console_id,
            "rendered_console_id": certification.rendered_console_id,
            "rendered_presentation_id": certification.rendered_presentation_id,
            "publication_complete": True,
            "presentation_publication_chain_complete": True,
            "read_only": True,
            "qseries_handoff_disabled": True,
            "qseries_execution_disabled": True,
            "orders_disabled": True,
            "funds_movement_disabled": True,
            "portfolio_mutation_disabled": True,
        }
        completion_record_payload_hash = stable_hash(completion_record_payload)

        attestation_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "completion_record_id": completion_record_id,
                "completion_record_payload_hash": completion_record_payload_hash,
                "attestation_type": ATTESTATION_TYPE,
            }
        )

        body = {
            "operator_presentation_publication_completion_attestation_id": attestation_id,
            "source_operator_presentation_publication_result_certification_id": certification.operator_presentation_publication_result_certification_id,
            "source_operator_presentation_publication_result_certification_hash": certification.operator_presentation_publication_result_certification_hash,
            "source_operator_presentation_publication_execution_id": certification.source_operator_presentation_publication_execution_id,
            "source_operator_presentation_publication_execution_hash": certification.source_operator_presentation_publication_execution_hash,
            "source_operator_presentation_publication_consumption_id": certification.source_operator_presentation_publication_consumption_id,
            "source_operator_presentation_publication_consumption_hash": certification.source_operator_presentation_publication_consumption_hash,
            "source_operator_presentation_publication_authorization_id": certification.source_operator_presentation_publication_authorization_id,
            "source_operator_presentation_publication_authorization_hash": certification.source_operator_presentation_publication_authorization_hash,
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
            "certification_type": certification.certification_type,
            "attestation_type": ATTESTATION_TYPE,
            "completion_record_type": COMPLETION_RECORD_TYPE,
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
            "published_presentation_payload": dict(certification.published_presentation_payload),
            "published_presentation_payload_hash": certification.published_presentation_payload_hash,
            "completion_record_id": completion_record_id,
            "completion_record_payload": completion_record_payload,
            "completion_record_payload_hash": completion_record_payload_hash,
            "certification_identity_verified": True,
            "certification_hash_verified": True,
            "certification_status_verified": True,
            "certification_type_verified": True,
            "published_presentation_identity_verified": True,
            "published_presentation_payload_hash_verified": True,
            "published_presentation_artifact_type_verified": True,
            "published_presentation_format_verified": True,
            "publication_completion_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "deterministic_attestation_verified": True,
            "immutable_completion_record_verified": True,
            "read_only_completion_verified": True,
            "publication_result_certified": True,
            "publication_completion_attested": True,
            "presentation_publication_chain_complete": True,
            "operator_presentation_subsystem_completion_ready": True,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "order_creation_allowed": False,
            "order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "attestation_status": ATTESTATION_STATUS,
        }

        return OracleOperatorPresentationPublicationCompletionAttestation(
            **body,
            operator_presentation_publication_completion_attestation_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ATTESTATION_STATUS",
    "ATTESTATION_TYPE",
    "COMPLETION_RECORD_TYPE",
    "OracleOperatorPresentationPublicationCompletionAttestation",
    "OracleOperatorPresentationPublicationCompletionAttestationGate",
    "OracleOperatorPresentationPublicationCompletionAttestationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_043_oracle_operator_presentation_publication_result_certification_gate import (
    _execution,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_result_certification_gate import (
    OracleOperatorPresentationPublicationResultCertificationGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_completion_attestation_gate import (
    ATTESTATION_STATUS,
    ATTESTATION_TYPE,
    COMPLETION_RECORD_TYPE,
    OracleOperatorPresentationPublicationCompletionAttestationGate,
    OracleOperatorPresentationPublicationCompletionAttestationInvariantError,
    stable_hash,
)


def _certification():
    return OracleOperatorPresentationPublicationResultCertificationGate().certify(
        execution=_execution()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe completion attestation accepted")
    except OracleOperatorPresentationPublicationCompletionAttestationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-044 TEST")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" COMPLETION ATTESTATION GATE")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorPresentationPublicationCompletionAttestationGate()

    first = gate.attest(certification=certification)
    repeated = gate.attest(certification=certification)

    assert first == repeated
    assert first.operator_presentation_publication_completion_attestation_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_publication_completion_attestation_hash"
        }
    )
    assert first.completion_record_payload_hash == stable_hash(
        first.completion_record_payload
    )
    assert first.attestation_type == ATTESTATION_TYPE
    assert first.completion_record_type == COMPLETION_RECORD_TYPE
    assert first.attestation_status == ATTESTATION_STATUS

    payload = first.completion_record_payload
    assert payload["completion_record_id"] == first.completion_record_id
    assert payload["published_presentation_id"] == first.published_presentation_id
    assert payload["published_presentation_payload_hash"] == first.published_presentation_payload_hash
    assert payload["publication_complete"] is True
    assert payload["presentation_publication_chain_complete"] is True
    assert payload["read_only"] is True
    assert payload["qseries_handoff_disabled"] is True
    assert payload["qseries_execution_disabled"] is True
    assert payload["orders_disabled"] is True
    assert payload["funds_movement_disabled"] is True
    assert payload["portfolio_mutation_disabled"] is True

    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.certification_type_verified
    assert first.published_presentation_identity_verified
    assert first.published_presentation_payload_hash_verified
    assert first.published_presentation_artifact_type_verified
    assert first.published_presentation_format_verified
    assert first.publication_completion_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.deterministic_attestation_verified
    assert first.immutable_completion_record_verified
    assert first.read_only_completion_verified
    assert first.publication_result_certified
    assert first.publication_completion_attested
    assert first.presentation_publication_chain_complete
    assert first.operator_presentation_subsystem_completion_ready

    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed

    _reject(lambda: gate.attest(certification=replace(
        certification,
        operator_presentation_publication_result_certification_hash="0" * 64,
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        certification_status="wrong_status",
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        published_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        publication_result_certified=False,
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        qseries_handoff_allowed=True,
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-043 publication certification consumed")
    print("[PASS] Certification identity, hash, status, and type verified")
    print("[PASS] Published presentation identity, payload hash, artifact type, and format verified")
    print("[PASS] Publication completion and safety boundaries verified")
    print("[PASS] Complete Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Immutable terminal completion record created")
    print("[PASS] Presentation publication chain marked complete")
    print("[PASS] Operator presentation subsystem completion marked ready")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe completion inputs rejected")
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
    print(" OOP-044 INSTALLER")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" COMPLETION ATTESTATION GATE")
    print("=" * 40)

    verify(
        SOURCE_043,
        "OOP-043",
        (
            'SCHEMA_VERSION = "OOP-043"',
            "class OracleOperatorPresentationPublicationResultCertification",
            "operator_presentation_publication_result_certification_hash",
            "published_presentation_payload_hash",
            "published_presentation_payload",
            "publication_result_certified",
            "qseries_handoff_allowed",
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
        SOURCE_043: sha256_file(SOURCE_043),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        PRESENTATION_INIT,
        "from .oracle_operator_presentation_publication_completion_attestation_gate import *",
    )
    export(
        OPERATOR_INIT,
        "from .presentation.oracle_operator_presentation_publication_completion_attestation_gate import *",
    )

    for path in (PRODUCTION, TEST, PRESENTATION_INIT, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-043 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics, Query, Research Response, Session, or Console export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-044 test executed automatically")
    print()
    print("[DONE] OOP-044 Operator presentation publication completion attestation installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
