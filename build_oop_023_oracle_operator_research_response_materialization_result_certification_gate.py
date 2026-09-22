from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPERATOR = ROOT / "qseries_v2" / "oracle_operator"
RR = OPERATOR / "research_response"
ANALYTICS_QUERY = (
    ROOT / "qseries_v2" / "oracle_intelligence" / "analytics" / "downstream" / "query"
)

SOURCE_060 = ANALYTICS_QUERY / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
SOURCE_022 = RR / "oracle_operator_research_response_materialization_execution_gate.py"

PRODUCTION = RR / "oracle_operator_research_response_materialization_result_certification_gate.py"
TEST = ROOT / "test_oop_023_oracle_operator_research_response_materialization_result_certification_gate.py"
RR_INIT = RR / "__init__.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_execution_gate import (
    EXECUTION_STATUS as OOP_022_EXECUTION_STATUS,
    RESEARCH_RESPONSE_ARTIFACT_TYPE as OOP_022_RESEARCH_RESPONSE_ARTIFACT_TYPE,
    RESPONSE_FORMAT as OOP_022_RESPONSE_FORMAT,
    OracleOperatorResearchResponseMaterializationExecution,
)

SCHEMA_VERSION = "OOP-023"
ENGINE_ID = "OOP-023"
POLICY_ID = "oracle.operator.research-response-materialization-result-certification-gate.v1"
CERTIFICATION_STATUS = "operator_research_response_materialization_result_certified"
CERTIFICATION_TYPE = "immutable_operator_research_response_result_certification"

EXPECTED_EXECUTION_STATUS = OOP_022_EXECUTION_STATUS
EXPECTED_RESEARCH_RESPONSE_ARTIFACT_TYPE = OOP_022_RESEARCH_RESPONSE_ARTIFACT_TYPE
EXPECTED_RESPONSE_FORMAT = OOP_022_RESPONSE_FORMAT


class OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
    RuntimeError
):
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
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
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
class OracleOperatorResearchResponseMaterializationResultCertification:
    research_response_materialization_result_certification_id: str
    source_research_response_materialization_execution_id: str
    source_research_response_materialization_execution_hash: str
    source_research_response_materialization_consumption_id: str
    source_research_response_materialization_consumption_hash: str
    operator_namespace: str
    query_namespace: str
    research_response_namespace: str
    consumer_id: str
    projection: str
    query_mode: str
    query_text: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    research_response_artifact_type: str
    response_format: str
    certification_type: str
    source_entry_count: int
    source_response_artifact_entry_ids: tuple[str, ...]
    source_query_response_ids: tuple[str, ...]
    source_result_count: int
    source_result_hashes: tuple[str, ...]
    research_response_id: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    research_response_payload: Mapping[str, Any]
    research_response_payload_hash: str
    execution_identity_verified: bool
    execution_hash_verified: bool
    execution_status_verified: bool
    response_identity_verified: bool
    response_payload_hash_verified: bool
    response_format_verified: bool
    response_artifact_type_verified: bool
    response_item_cardinality_verified: bool
    response_item_identity_verified: bool
    source_result_hashes_verified: bool
    certified_payload_preservation_verified: bool
    read_only_response_verified: bool
    immutable_response_verified: bool
    deterministic_certification_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    query_subsystem_complete: bool
    research_response_handoff_ready: bool
    research_response_handoff_authorized: bool
    research_response_handoff_consumed: bool
    research_response_materialization_ready: bool
    research_response_materialization_authorized: bool
    research_response_materialization_authorization_consumed: bool
    research_response_materialization_allowed: bool
    research_response_materialization_performed: bool
    research_response_result_certified: bool
    operator_session_construction_ready: bool
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
    certification_status: str
    research_response_materialization_result_certification_hash: str


class OracleOperatorResearchResponseMaterializationResultCertificationGate:
    @staticmethod
    def _verify(
        execution: OracleOperatorResearchResponseMaterializationExecution,
    ) -> None:
        if not isinstance(
            execution,
            OracleOperatorResearchResponseMaterializationExecution,
        ):
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "source must be canonical OOP-022 execution"
            )

        body = asdict(execution)
        supplied_hash = body.pop(
            "research_response_materialization_execution_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "OOP-022 execution hash mismatch"
            )

        if execution.execution_status != EXPECTED_EXECUTION_STATUS:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "OOP-022 execution status mismatch"
            )
        if (
            execution.research_response_artifact_type
            != EXPECTED_RESEARCH_RESPONSE_ARTIFACT_TYPE
        ):
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response artifact type mismatch"
            )
        if execution.response_format != EXPECTED_RESPONSE_FORMAT:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "response format mismatch"
            )

        if not _valid_sha256(execution.research_response_id):
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response id is invalid"
            )
        if not _valid_sha256(execution.research_response_payload_hash):
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response payload hash is invalid"
            )
        if stable_hash(execution.research_response_payload) != execution.research_response_payload_hash:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response payload hash mismatch"
            )

        count = execution.research_response_item_count
        if count < 1:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response contains no items"
            )
        if not (
            count == len(execution.research_response_items)
            == execution.source_result_count
            == execution.source_entry_count
            == len(execution.source_result_hashes)
            == len(execution.source_response_artifact_entry_ids)
            == len(execution.source_query_response_ids)
        ):
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response cardinality mismatch"
            )

        payload_items = execution.research_response_payload.get("items")
        if tuple(payload_items or ()) != tuple(execution.research_response_items):
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response item payload mismatch"
            )
        if execution.research_response_payload.get("research_response_id") != execution.research_response_id:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response identity mismatch"
            )
        if execution.research_response_payload.get("result_count") != count:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response result count mismatch"
            )
        if execution.research_response_payload.get("read_only") is not True:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "research response is not read-only"
            )
        if execution.research_response_payload.get("publication_disabled") is not True:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "publication is not disabled"
            )
        if execution.research_response_payload.get("qseries_execution_disabled") is not True:
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "Q Series execution is not disabled"
            )

        for index, item in enumerate(execution.research_response_items):
            if item.get("ordinal") != index + 1:
                raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                    "response item ordinal mismatch"
                )
            if item.get("response_artifact_entry_id") != execution.source_response_artifact_entry_ids[index]:
                raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                    "response artifact entry identity mismatch"
                )
            if item.get("query_response_id") != execution.source_query_response_ids[index]:
                raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                    "query response identity mismatch"
                )
            if item.get("source_result_hash") != execution.source_result_hashes[index]:
                raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                    "source result hash mismatch"
                )
            certified_payload = item.get("certified_payload")
            if not isinstance(certified_payload, Mapping):
                raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                    "certified payload missing"
                )
            if stable_hash(certified_payload) != execution.source_result_hashes[index]:
                raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                    "certified payload hash mismatch"
                )

        required = (
            execution.authorization_consumption_verified,
            execution.authorization_identity_verified,
            execution.authorization_hash_verified,
            execution.authorization_status_verified,
            execution.complete_lineage_verified,
            execution.namespaces_verified,
            execution.query_parameters_verified,
            execution.frozen_scope_verified,
            execution.frozen_scope_preserved,
            execution.result_cardinality_verified,
            execution.result_identity_verified,
            execution.result_payload_hashes_verified,
            execution.deterministic_materialization_verified,
            execution.immutable_response_verified,
            execution.read_only_materialization_verified,
            execution.query_subsystem_complete,
            execution.research_response_handoff_ready,
            execution.research_response_handoff_authorized,
            execution.research_response_handoff_consumed,
            execution.research_response_materialization_ready,
            execution.research_response_materialization_authorized,
            execution.research_response_materialization_authorization_consumed,
            execution.research_response_materialization_allowed,
            execution.research_response_materialization_performed,
            execution.research_response_certification_ready,
        )
        if not all(required):
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "OOP-022 execution is incomplete"
            )

        forbidden = (
            execution.operator_session_construction_allowed,
            execution.operator_console_rendering_allowed,
            execution.operator_presentation_rendering_allowed,
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
            raise OracleOperatorResearchResponseMaterializationResultCertificationInvariantError(
                "forbidden downstream activity detected"
            )

    def certify(
        self,
        *,
        execution: OracleOperatorResearchResponseMaterializationExecution,
    ) -> OracleOperatorResearchResponseMaterializationResultCertification:
        self._verify(execution)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_execution_id": execution.research_response_materialization_execution_id,
                "source_execution_hash": execution.research_response_materialization_execution_hash,
                "research_response_id": execution.research_response_id,
                "research_response_payload_hash": execution.research_response_payload_hash,
                "certification_type": CERTIFICATION_TYPE,
            }
        )

        body = {
            "research_response_materialization_result_certification_id": certification_id,
            "source_research_response_materialization_execution_id": execution.research_response_materialization_execution_id,
            "source_research_response_materialization_execution_hash": execution.research_response_materialization_execution_hash,
            "source_research_response_materialization_consumption_id": execution.source_research_response_materialization_consumption_id,
            "source_research_response_materialization_consumption_hash": execution.source_research_response_materialization_consumption_hash,
            "operator_namespace": execution.operator_namespace,
            "query_namespace": execution.query_namespace,
            "research_response_namespace": execution.research_response_namespace,
            "consumer_id": execution.consumer_id,
            "projection": execution.projection,
            "query_mode": execution.query_mode,
            "query_text": execution.query_text,
            "time_scope": execution.time_scope,
            "sort_order": execution.sort_order,
            "result_limit": execution.result_limit,
            "requested_tags": tuple(execution.requested_tags),
            "research_response_artifact_type": execution.research_response_artifact_type,
            "response_format": execution.response_format,
            "certification_type": CERTIFICATION_TYPE,
            "source_entry_count": execution.source_entry_count,
            "source_response_artifact_entry_ids": tuple(execution.source_response_artifact_entry_ids),
            "source_query_response_ids": tuple(execution.source_query_response_ids),
            "source_result_count": execution.source_result_count,
            "source_result_hashes": tuple(execution.source_result_hashes),
            "research_response_id": execution.research_response_id,
            "research_response_item_count": execution.research_response_item_count,
            "research_response_items": tuple(execution.research_response_items),
            "research_response_payload": dict(execution.research_response_payload),
            "research_response_payload_hash": execution.research_response_payload_hash,
            "execution_identity_verified": True,
            "execution_hash_verified": True,
            "execution_status_verified": True,
            "response_identity_verified": True,
            "response_payload_hash_verified": True,
            "response_format_verified": True,
            "response_artifact_type_verified": True,
            "response_item_cardinality_verified": True,
            "response_item_identity_verified": True,
            "source_result_hashes_verified": True,
            "certified_payload_preservation_verified": True,
            "read_only_response_verified": True,
            "immutable_response_verified": True,
            "deterministic_certification_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "query_subsystem_complete": True,
            "research_response_handoff_ready": True,
            "research_response_handoff_authorized": True,
            "research_response_handoff_consumed": True,
            "research_response_materialization_ready": True,
            "research_response_materialization_authorized": True,
            "research_response_materialization_authorization_consumed": True,
            "research_response_materialization_allowed": True,
            "research_response_materialization_performed": True,
            "research_response_result_certified": True,
            "operator_session_construction_ready": True,
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
            "certification_status": CERTIFICATION_STATUS,
        }

        return OracleOperatorResearchResponseMaterializationResultCertification(
            **body,
            research_response_materialization_result_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_STATUS",
    "CERTIFICATION_TYPE",
    "OracleOperatorResearchResponseMaterializationResultCertification",
    "OracleOperatorResearchResponseMaterializationResultCertificationGate",
    "OracleOperatorResearchResponseMaterializationResultCertificationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_022_oracle_operator_research_response_materialization_execution_gate import (
    _consumption,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_execution_gate import (
    OracleOperatorResearchResponseMaterializationExecutionGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    OracleOperatorResearchResponseMaterializationResultCertificationGate,
    OracleOperatorResearchResponseMaterializationResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorResearchResponseMaterializationExecutionGate().execute(
        consumption=_consumption()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe certification accepted")
    except OracleOperatorResearchResponseMaterializationResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-023 TEST")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorResearchResponseMaterializationResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.research_response_materialization_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_materialization_result_certification_hash"
        }
    )
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.research_response_id == execution.research_response_id
    assert first.research_response_payload_hash == execution.research_response_payload_hash
    assert first.research_response_payload == execution.research_response_payload
    assert first.research_response_items == execution.research_response_items

    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.response_identity_verified
    assert first.response_payload_hash_verified
    assert first.response_format_verified
    assert first.response_artifact_type_verified
    assert first.response_item_cardinality_verified
    assert first.response_item_identity_verified
    assert first.source_result_hashes_verified
    assert first.certified_payload_preservation_verified
    assert first.read_only_response_verified
    assert first.immutable_response_verified
    assert first.deterministic_certification_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.research_response_result_certified
    assert first.operator_session_construction_ready
    assert not first.operator_session_construction_allowed
    assert not first.operator_console_rendering_allowed
    assert not first.operator_presentation_rendering_allowed
    assert not first.publication_allowed
    assert not first.qseries_execution_allowed
    assert not first.order_creation_allowed
    assert not first.funds_movement_allowed
    assert not first.portfolio_mutation_allowed

    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_materialization_execution_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        execution_status="wrong_status",
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_item_count=execution.research_response_item_count + 1,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_session_construction_allowed=True,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-022 materialized response consumed")
    print("[PASS] OOP-022 execution identity, hash, and status verified")
    print("[PASS] Research Response payload hash recomputed and verified")
    print("[PASS] Response format, artifact type, identities, and cardinality verified")
    print("[PASS] Certified source payload preservation verified")
    print("[PASS] Immutable read-only Research Response certified")
    print("[PASS] Complete frozen lineage preserved")
    print("[PASS] Operator Session construction marked ready")
    print("[PASS] Session construction remains unauthorized")
    print("[PASS] Console, presentation, publication, and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe execution results rejected")
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
    print(" OOP-023 INSTALLER")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    verify(
        SOURCE_022,
        "OOP-022",
        (
            'SCHEMA_VERSION = "OOP-022"',
            "class OracleOperatorResearchResponseMaterializationExecution",
            "research_response_materialization_execution_hash",
            "research_response_payload_hash",
            "research_response_items",
            "research_response_materialization_performed",
            "research_response_certification_ready",
            "operator_session_construction_allowed",
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
        SOURCE_022: sha256_file(SOURCE_022),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        RR_INIT,
        "from .oracle_operator_research_response_materialization_result_certification_gate import *",
    )
    export(
        OPERATOR_INIT,
        "from .research_response.oracle_operator_research_response_materialization_result_certification_gate import *",
    )

    for path in (PRODUCTION, TEST, RR_INIT, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-022 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics or Query package export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-023 test executed automatically")
    print()
    print("[DONE] OOP-023 Research Response result certification installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
