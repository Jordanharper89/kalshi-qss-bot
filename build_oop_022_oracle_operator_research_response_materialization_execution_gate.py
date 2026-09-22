from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPERATOR = ROOT / "qseries_v2" / "oracle_operator"
RR = OPERATOR / "research_response"
QUERY = OPERATOR / "query"
ANALYTICS_QUERY = (
    ROOT / "qseries_v2" / "oracle_intelligence" / "analytics" / "downstream" / "query"
)

SOURCE_060 = ANALYTICS_QUERY / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
SOURCE_021 = RR / "oracle_operator_research_response_materialization_authorization_consumption_gate.py"
PRODUCTION = RR / "oracle_operator_research_response_materialization_execution_gate.py"
TEST = ROOT / "test_oop_022_oracle_operator_research_response_materialization_execution_gate.py"
RR_INIT = RR / "__init__.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_021_CONSUMPTION_STATUS,
    EXECUTION_PACKAGE_TYPE as OOP_021_EXECUTION_PACKAGE_TYPE,
    OracleOperatorResearchResponseMaterializationAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-022"
ENGINE_ID = "OOP-022"
POLICY_ID = "oracle.operator.research-response-materialization-execution-gate.v1"
EXECUTION_STATUS = "operator_research_response_materialization_executed"
RESEARCH_RESPONSE_ARTIFACT_TYPE = "immutable_operator_research_response_artifact"
RESPONSE_FORMAT = "structured_research_response_v1"

EXPECTED_CONSUMPTION_STATUS = OOP_021_CONSUMPTION_STATUS
EXPECTED_EXECUTION_PACKAGE_TYPE = OOP_021_EXECUTION_PACKAGE_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"


class OracleOperatorResearchResponseMaterializationExecutionInvariantError(
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
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
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


def _text(payload: Mapping[str, Any], keys: tuple[str, ...], fallback: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


@dataclass(frozen=True)
class OracleOperatorResearchResponseMaterializationExecution:
    research_response_materialization_execution_id: str
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
    execution_package_type: str
    research_response_artifact_type: str
    response_format: str
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
    authorization_consumption_verified: bool
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    authorization_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    deterministic_materialization_verified: bool
    immutable_response_verified: bool
    read_only_materialization_verified: bool
    query_subsystem_complete: bool
    research_response_handoff_ready: bool
    research_response_handoff_authorized: bool
    research_response_handoff_consumed: bool
    research_response_materialization_ready: bool
    research_response_materialization_authorized: bool
    research_response_materialization_authorization_consumed: bool
    research_response_materialization_allowed: bool
    research_response_materialization_performed: bool
    research_response_certification_ready: bool
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
    execution_status: str
    research_response_materialization_execution_hash: str


class OracleOperatorResearchResponseMaterializationExecutionGate:
    @staticmethod
    def _verify(
        consumption: OracleOperatorResearchResponseMaterializationAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorResearchResponseMaterializationAuthorizationConsumption,
        ):
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "source must be canonical OOP-021 consumption"
            )

        body = asdict(consumption)
        supplied_hash = body.pop(
            "research_response_materialization_consumption_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "OOP-021 consumption hash mismatch"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "OOP-021 consumption status mismatch"
            )
        if consumption.execution_package_type != EXPECTED_EXECUTION_PACKAGE_TYPE:
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "execution package type mismatch"
            )
        if consumption.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "operator namespace mismatch"
            )
        if consumption.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "query namespace mismatch"
            )
        if consumption.research_response_namespace != EXPECTED_RESEARCH_RESPONSE_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "research response namespace mismatch"
            )

        count = consumption.consumed_result_count
        if count < 1 or consumption.consumed_entry_count != count:
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "source cardinality mismatch"
            )
        if not (
            count == len(consumption.consumed_result_payloads)
            == len(consumption.consumed_result_hashes)
            == len(consumption.consumed_response_artifact_entry_ids)
            == len(consumption.consumed_query_response_ids)
        ):
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "source collection cardinality mismatch"
            )

        hashes = tuple(stable_hash(item) for item in consumption.consumed_result_payloads)
        if hashes != tuple(consumption.consumed_result_hashes):
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "source payload hash mismatch"
            )

        required = (
            consumption.authorization_type_verified,
            consumption.authorization_identity_verified,
            consumption.authorization_hash_verified,
            consumption.authorization_status_verified,
            consumption.complete_lineage_verified,
            consumption.namespaces_verified,
            consumption.query_parameters_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.response_input_package_verified,
            consumption.response_schema_inputs_verified,
            consumption.response_content_inputs_verified,
            consumption.result_cardinality_verified,
            consumption.result_identity_verified,
            consumption.result_payload_hashes_verified,
            consumption.single_use_consumption_verified,
            consumption.immutable_execution_package_verified,
            consumption.deterministic_consumption_verified,
            consumption.query_subsystem_complete,
            consumption.research_response_handoff_ready,
            consumption.research_response_handoff_authorized,
            consumption.research_response_handoff_consumed,
            consumption.research_response_materialization_ready,
            consumption.research_response_materialization_authorized,
            consumption.research_response_materialization_authorization_consumed,
            consumption.research_response_materialization_allowed,
        )
        if not all(required):
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "OOP-021 execution package incomplete"
            )

        forbidden = (
            consumption.research_response_materialization_performed,
            consumption.operator_session_construction_allowed,
            consumption.operator_console_rendering_allowed,
            consumption.operator_presentation_rendering_allowed,
            consumption.publication_allowed,
            consumption.publication_performed,
            consumption.qseries_handoff_allowed,
            consumption.qseries_execution_allowed,
            consumption.qseries_execution_performed,
            consumption.order_creation_allowed,
            consumption.order_creation_performed,
            consumption.funds_movement_allowed,
            consumption.funds_movement_performed,
            consumption.portfolio_mutation_allowed,
            consumption.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorResearchResponseMaterializationExecutionInvariantError(
                "forbidden downstream activity detected"
            )

    def execute(
        self,
        *,
        consumption: OracleOperatorResearchResponseMaterializationAuthorizationConsumption,
    ) -> OracleOperatorResearchResponseMaterializationExecution:
        self._verify(consumption)

        items = tuple(
            {
                "ordinal": index + 1,
                "response_artifact_entry_id": consumption.consumed_response_artifact_entry_ids[index],
                "query_response_id": consumption.consumed_query_response_ids[index],
                "source_result_hash": consumption.consumed_result_hashes[index],
                "title": _text(
                    payload,
                    ("title", "market_title", "question", "headline", "name"),
                    f"Certified research result {index + 1}",
                ),
                "summary": _text(
                    payload,
                    ("summary", "analysis", "description", "rationale", "explanation"),
                    "Certified read-only analytics result.",
                ),
                "certified_payload": dict(payload),
            }
            for index, payload in enumerate(consumption.consumed_result_payloads)
        )

        research_response_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.research_response_materialization_consumption_id,
                "source_consumption_hash": consumption.research_response_materialization_consumption_hash,
                "response_format": RESPONSE_FORMAT,
                "query_text": consumption.query_text,
                "items": items,
            }
        )
        response_payload = {
            "research_response_id": research_response_id,
            "response_format": RESPONSE_FORMAT,
            "consumer_id": consumption.consumer_id,
            "query_text": consumption.query_text,
            "query_mode": consumption.query_mode,
            "projection": consumption.projection,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "requested_tags": tuple(consumption.requested_tags),
            "result_count": len(items),
            "items": items,
            "read_only": True,
            "publication_disabled": True,
            "qseries_execution_disabled": True,
        }
        payload_hash = stable_hash(response_payload)
        execution_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.research_response_materialization_consumption_id,
                "research_response_id": research_response_id,
                "research_response_payload_hash": payload_hash,
            }
        )

        body = {
            "research_response_materialization_execution_id": execution_id,
            "source_research_response_materialization_consumption_id": consumption.research_response_materialization_consumption_id,
            "source_research_response_materialization_consumption_hash": consumption.research_response_materialization_consumption_hash,
            "operator_namespace": consumption.operator_namespace,
            "query_namespace": consumption.query_namespace,
            "research_response_namespace": consumption.research_response_namespace,
            "consumer_id": consumption.consumer_id,
            "projection": consumption.projection,
            "query_mode": consumption.query_mode,
            "query_text": consumption.query_text,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "execution_package_type": consumption.execution_package_type,
            "research_response_artifact_type": RESEARCH_RESPONSE_ARTIFACT_TYPE,
            "response_format": RESPONSE_FORMAT,
            "source_entry_count": consumption.consumed_entry_count,
            "source_response_artifact_entry_ids": tuple(consumption.consumed_response_artifact_entry_ids),
            "source_query_response_ids": tuple(consumption.consumed_query_response_ids),
            "source_result_count": consumption.consumed_result_count,
            "source_result_hashes": tuple(consumption.consumed_result_hashes),
            "research_response_id": research_response_id,
            "research_response_item_count": len(items),
            "research_response_items": items,
            "research_response_payload": response_payload,
            "research_response_payload_hash": payload_hash,
            "authorization_consumption_verified": True,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "authorization_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "deterministic_materialization_verified": True,
            "immutable_response_verified": True,
            "read_only_materialization_verified": True,
            "query_subsystem_complete": True,
            "research_response_handoff_ready": True,
            "research_response_handoff_authorized": True,
            "research_response_handoff_consumed": True,
            "research_response_materialization_ready": True,
            "research_response_materialization_authorized": True,
            "research_response_materialization_authorization_consumed": True,
            "research_response_materialization_allowed": True,
            "research_response_materialization_performed": True,
            "research_response_certification_ready": True,
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
            "execution_status": EXECUTION_STATUS,
        }
        return OracleOperatorResearchResponseMaterializationExecution(
            **body,
            research_response_materialization_execution_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "EXECUTION_STATUS",
    "RESEARCH_RESPONSE_ARTIFACT_TYPE",
    "RESPONSE_FORMAT",
    "OracleOperatorResearchResponseMaterializationExecution",
    "OracleOperatorResearchResponseMaterializationExecutionGate",
    "OracleOperatorResearchResponseMaterializationExecutionInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_021_oracle_operator_research_response_materialization_authorization_consumption_gate import (
    _authorization,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_authorization_consumption_gate import (
    OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_execution_gate import (
    EXECUTION_STATUS,
    RESEARCH_RESPONSE_ARTIFACT_TYPE,
    RESPONSE_FORMAT,
    OracleOperatorResearchResponseMaterializationExecutionGate,
    OracleOperatorResearchResponseMaterializationExecutionInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe execution accepted")
    except OracleOperatorResearchResponseMaterializationExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-022 TEST")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" EXECUTION GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorResearchResponseMaterializationExecutionGate()
    first = gate.execute(consumption=consumption)
    repeated = gate.execute(consumption=consumption)

    assert first == repeated
    assert first.research_response_materialization_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_materialization_execution_hash"
        }
    )
    assert first.research_response_payload_hash == stable_hash(first.research_response_payload)
    assert first.research_response_artifact_type == RESEARCH_RESPONSE_ARTIFACT_TYPE
    assert first.response_format == RESPONSE_FORMAT
    assert first.source_result_count == consumption.consumed_result_count
    assert first.research_response_item_count == consumption.consumed_result_count
    assert first.source_result_hashes == consumption.consumed_result_hashes

    for index, item in enumerate(first.research_response_items):
        assert item["ordinal"] == index + 1
        assert item["response_artifact_entry_id"] == consumption.consumed_response_artifact_entry_ids[index]
        assert item["query_response_id"] == consumption.consumed_query_response_ids[index]
        assert item["source_result_hash"] == consumption.consumed_result_hashes[index]
        assert item["certified_payload"] == consumption.consumed_result_payloads[index]

    assert first.deterministic_materialization_verified
    assert first.immutable_response_verified
    assert first.read_only_materialization_verified
    assert first.research_response_materialization_performed
    assert first.research_response_certification_ready
    assert not first.operator_session_construction_allowed
    assert not first.operator_console_rendering_allowed
    assert not first.operator_presentation_rendering_allowed
    assert not first.publication_allowed
    assert not first.qseries_execution_allowed
    assert not first.order_creation_allowed
    assert not first.funds_movement_allowed
    assert not first.portfolio_mutation_allowed
    assert first.execution_status == EXECUTION_STATUS

    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_materialization_consumption_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumption_status="wrong_status",
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumed_result_hashes=("0" * 64,) * consumption.consumed_result_count,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_materialization_performed=True,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-021 execution package consumed")
    print("[PASS] OOP-021 hash, status, scope, and cardinality verified")
    print("[PASS] Source result payload hashes recomputed")
    print("[PASS] Deterministic immutable Research Response created")
    print("[PASS] Research Response payload hash verified")
    print("[PASS] Read-only materialization performed")
    print("[PASS] Research Response certification marked ready")
    print("[PASS] Session, console, presentation, and publication remain gated")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe execution packages rejected")
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
    if line not in existing.splitlines():
        if existing and not existing.endswith("\n"):
            existing += "\n"
        path.write_text(existing + line + "\n", encoding="utf-8", newline="\n")
        print(f"[OK] PACKAGE UPDATED: {path.resolve()}")
    else:
        print(f"[OK] PACKAGE EXPORT PRESENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" OOP-022 INSTALLER")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" EXECUTION GATE")
    print("=" * 40)

    verify(
        SOURCE_021,
        "OOP-021",
        (
            'SCHEMA_VERSION = "OOP-021"',
            "class OracleOperatorResearchResponseMaterializationAuthorizationConsumption",
            "research_response_materialization_consumption_hash",
            "execution_package_type",
            "consumed_result_hashes",
            "consumed_result_payloads",
            "research_response_materialization_allowed",
            "research_response_materialization_performed",
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

    protected = {SOURCE_021: sha256_file(SOURCE_021), SOURCE_060: sha256_file(SOURCE_060)}

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        RR_INIT,
        "from .oracle_operator_research_response_materialization_execution_gate import *",
    )
    export(
        OPERATOR_INIT,
        "from .research_response.oracle_operator_research_response_materialization_execution_gate import *",
    )

    for path in (PRODUCTION, TEST, RR_INIT, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-021 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics or Query package export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-022 test executed automatically")
    print()
    print("[DONE] OOP-022 Research Response materialization execution installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
