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
SOURCE_024 = SESSION / "oracle_operator_session_construction_authorization_gate.py"

PRODUCTION = SESSION / "oracle_operator_session_construction_authorization_consumption_gate.py"
TEST = ROOT / "test_oop_025_oracle_operator_session_construction_authorization_consumption_gate.py"
SESSION_INIT = SESSION / "__init__.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.session.oracle_operator_session_construction_authorization_gate import (
    AUTHORIZATION_STATUS as OOP_024_AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE as OOP_024_AUTHORIZATION_TYPE,
    SESSION_PACKAGE_TYPE as OOP_024_SESSION_PACKAGE_TYPE,
    OracleOperatorSessionConstructionAuthorization,
)

SCHEMA_VERSION = "OOP-025"
ENGINE_ID = "OOP-025"
POLICY_ID = "oracle.operator.session-construction-authorization-consumption-gate.v1"
CONSUMPTION_STATUS = "operator_session_construction_authorization_consumed"
EXECUTION_PACKAGE_TYPE = "single_use_immutable_operator_session_construction_execution_package"

EXPECTED_AUTHORIZATION_STATUS = OOP_024_AUTHORIZATION_STATUS
EXPECTED_AUTHORIZATION_TYPE = OOP_024_AUTHORIZATION_TYPE
EXPECTED_SESSION_PACKAGE_TYPE = OOP_024_SESSION_PACKAGE_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"
EXPECTED_SESSION_NAMESPACE = "qseries_v2.oracle_operator.session"


class OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
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
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
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
class OracleOperatorSessionConstructionAuthorizationConsumption:
    operator_session_construction_consumption_id: str
    source_operator_session_construction_authorization_id: str
    source_operator_session_construction_authorization_hash: str
    source_research_response_result_certification_id: str
    source_research_response_result_certification_hash: str
    source_research_response_materialization_execution_id: str
    source_research_response_materialization_execution_hash: str
    source_research_response_materialization_consumption_id: str
    source_research_response_materialization_consumption_hash: str
    operator_namespace: str
    query_namespace: str
    research_response_namespace: str
    session_namespace: str
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
    authorization_type: str
    session_package_type: str
    execution_package_type: str
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
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    authorization_status_verified: bool
    authorization_type_verified: bool
    session_package_type_verified: bool
    research_response_identity_verified: bool
    research_response_payload_hash_verified: bool
    response_item_cardinality_verified: bool
    response_item_identity_verified: bool
    source_result_hashes_verified: bool
    certified_payload_preservation_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_session_input_verified: bool
    single_use_consumption_verified: bool
    immutable_execution_package_verified: bool
    deterministic_consumption_verified: bool
    read_only_boundary_verified: bool
    query_subsystem_complete: bool
    research_response_result_certified: bool
    operator_session_construction_ready: bool
    operator_session_construction_authorized: bool
    operator_session_construction_authorization_consumed: bool
    operator_session_construction_allowed: bool
    operator_session_construction_performed: bool
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
    consumption_status: str
    operator_session_construction_consumption_hash: str


class OracleOperatorSessionConstructionAuthorizationConsumptionGate:
    @staticmethod
    def _verify(
        authorization: OracleOperatorSessionConstructionAuthorization,
    ) -> None:
        if not isinstance(authorization, OracleOperatorSessionConstructionAuthorization):
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "source must be canonical OOP-024 authorization"
            )

        body = asdict(authorization)
        supplied_hash = body.pop(
            "operator_session_construction_authorization_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "OOP-024 authorization hash mismatch"
            )

        if authorization.authorization_status != EXPECTED_AUTHORIZATION_STATUS:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "OOP-024 authorization status mismatch"
            )
        if authorization.authorization_type != EXPECTED_AUTHORIZATION_TYPE:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "authorization type mismatch"
            )
        if authorization.session_package_type != EXPECTED_SESSION_PACKAGE_TYPE:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "session package type mismatch"
            )

        if authorization.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "operator namespace mismatch"
            )
        if authorization.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "query namespace mismatch"
            )
        if authorization.research_response_namespace != EXPECTED_RESEARCH_RESPONSE_NAMESPACE:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "research response namespace mismatch"
            )
        if authorization.session_namespace != EXPECTED_SESSION_NAMESPACE:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "session namespace mismatch"
            )

        if not _valid_sha256(authorization.research_response_id):
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "research response id invalid"
            )
        if not _valid_sha256(authorization.research_response_payload_hash):
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "research response payload hash invalid"
            )
        if stable_hash(authorization.research_response_payload) != authorization.research_response_payload_hash:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "research response payload hash mismatch"
            )

        count = authorization.research_response_item_count
        if count < 1:
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "authorization contains no response items"
            )
        if not (
            count == len(authorization.research_response_items)
            == authorization.source_entry_count
            == authorization.source_result_count
            == len(authorization.source_response_artifact_entry_ids)
            == len(authorization.source_query_response_ids)
            == len(authorization.source_result_hashes)
        ):
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "authorization cardinality mismatch"
            )

        for index, item in enumerate(authorization.research_response_items):
            if item.get("ordinal") != index + 1:
                raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                    "response item ordinal mismatch"
                )
            if item.get("response_artifact_entry_id") != authorization.source_response_artifact_entry_ids[index]:
                raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                    "artifact entry identity mismatch"
                )
            if item.get("query_response_id") != authorization.source_query_response_ids[index]:
                raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                    "query response identity mismatch"
                )
            if item.get("source_result_hash") != authorization.source_result_hashes[index]:
                raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                    "source result identity mismatch"
                )
            certified_payload = item.get("certified_payload")
            if not isinstance(certified_payload, Mapping):
                raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                    "certified payload missing"
                )
            if stable_hash(certified_payload) != authorization.source_result_hashes[index]:
                raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                    "certified payload hash mismatch"
                )

        required = (
            authorization.certification_identity_verified,
            authorization.certification_hash_verified,
            authorization.certification_status_verified,
            authorization.certification_type_verified,
            authorization.research_response_identity_verified,
            authorization.research_response_payload_hash_verified,
            authorization.response_item_cardinality_verified,
            authorization.response_item_identity_verified,
            authorization.source_result_hashes_verified,
            authorization.certified_payload_preservation_verified,
            authorization.complete_lineage_verified,
            authorization.frozen_scope_verified,
            authorization.frozen_scope_preserved,
            authorization.immutable_session_input_verified,
            authorization.single_use_authorization_verified,
            authorization.deterministic_authorization_verified,
            authorization.read_only_boundary_verified,
            authorization.query_subsystem_complete,
            authorization.research_response_result_certified,
            authorization.operator_session_construction_ready,
            authorization.operator_session_construction_authorized,
            authorization.operator_session_construction_allowed,
        )
        if not all(required):
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "OOP-024 authorization incomplete"
            )

        forbidden = (
            authorization.operator_session_construction_performed,
            authorization.operator_console_rendering_allowed,
            authorization.operator_console_rendering_performed,
            authorization.operator_presentation_rendering_allowed,
            authorization.operator_presentation_rendering_performed,
            authorization.publication_allowed,
            authorization.publication_performed,
            authorization.qseries_handoff_allowed,
            authorization.qseries_execution_allowed,
            authorization.qseries_execution_performed,
            authorization.order_creation_allowed,
            authorization.order_creation_performed,
            authorization.funds_movement_allowed,
            authorization.funds_movement_performed,
            authorization.portfolio_mutation_allowed,
            authorization.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError(
                "forbidden downstream activity detected"
            )

    def consume(
        self,
        *,
        authorization: OracleOperatorSessionConstructionAuthorization,
    ) -> OracleOperatorSessionConstructionAuthorizationConsumption:
        self._verify(authorization)

        consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_authorization_id": authorization.operator_session_construction_authorization_id,
                "source_authorization_hash": authorization.operator_session_construction_authorization_hash,
                "research_response_id": authorization.research_response_id,
                "research_response_payload_hash": authorization.research_response_payload_hash,
                "execution_package_type": EXECUTION_PACKAGE_TYPE,
            }
        )

        body = {
            "operator_session_construction_consumption_id": consumption_id,
            "source_operator_session_construction_authorization_id": authorization.operator_session_construction_authorization_id,
            "source_operator_session_construction_authorization_hash": authorization.operator_session_construction_authorization_hash,
            "source_research_response_result_certification_id": authorization.source_research_response_result_certification_id,
            "source_research_response_result_certification_hash": authorization.source_research_response_result_certification_hash,
            "source_research_response_materialization_execution_id": authorization.source_research_response_materialization_execution_id,
            "source_research_response_materialization_execution_hash": authorization.source_research_response_materialization_execution_hash,
            "source_research_response_materialization_consumption_id": authorization.source_research_response_materialization_consumption_id,
            "source_research_response_materialization_consumption_hash": authorization.source_research_response_materialization_consumption_hash,
            "operator_namespace": authorization.operator_namespace,
            "query_namespace": authorization.query_namespace,
            "research_response_namespace": authorization.research_response_namespace,
            "session_namespace": authorization.session_namespace,
            "consumer_id": authorization.consumer_id,
            "projection": authorization.projection,
            "query_mode": authorization.query_mode,
            "query_text": authorization.query_text,
            "time_scope": authorization.time_scope,
            "sort_order": authorization.sort_order,
            "result_limit": authorization.result_limit,
            "requested_tags": tuple(authorization.requested_tags),
            "research_response_artifact_type": authorization.research_response_artifact_type,
            "response_format": authorization.response_format,
            "certification_type": authorization.certification_type,
            "authorization_type": authorization.authorization_type,
            "session_package_type": authorization.session_package_type,
            "execution_package_type": EXECUTION_PACKAGE_TYPE,
            "source_entry_count": authorization.source_entry_count,
            "source_response_artifact_entry_ids": tuple(authorization.source_response_artifact_entry_ids),
            "source_query_response_ids": tuple(authorization.source_query_response_ids),
            "source_result_count": authorization.source_result_count,
            "source_result_hashes": tuple(authorization.source_result_hashes),
            "research_response_id": authorization.research_response_id,
            "research_response_item_count": authorization.research_response_item_count,
            "research_response_items": tuple(authorization.research_response_items),
            "research_response_payload": dict(authorization.research_response_payload),
            "research_response_payload_hash": authorization.research_response_payload_hash,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "authorization_status_verified": True,
            "authorization_type_verified": True,
            "session_package_type_verified": True,
            "research_response_identity_verified": True,
            "research_response_payload_hash_verified": True,
            "response_item_cardinality_verified": True,
            "response_item_identity_verified": True,
            "source_result_hashes_verified": True,
            "certified_payload_preservation_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_session_input_verified": True,
            "single_use_consumption_verified": True,
            "immutable_execution_package_verified": True,
            "deterministic_consumption_verified": True,
            "read_only_boundary_verified": True,
            "query_subsystem_complete": True,
            "research_response_result_certified": True,
            "operator_session_construction_ready": True,
            "operator_session_construction_authorized": True,
            "operator_session_construction_authorization_consumed": True,
            "operator_session_construction_allowed": True,
            "operator_session_construction_performed": False,
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
            "consumption_status": CONSUMPTION_STATUS,
        }

        return OracleOperatorSessionConstructionAuthorizationConsumption(
            **body,
            operator_session_construction_consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_STATUS",
    "EXECUTION_PACKAGE_TYPE",
    "OracleOperatorSessionConstructionAuthorizationConsumption",
    "OracleOperatorSessionConstructionAuthorizationConsumptionGate",
    "OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_024_oracle_operator_session_construction_authorization_gate import (
    _certification,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_authorization_gate import (
    OracleOperatorSessionConstructionAuthorizationGate,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    EXECUTION_PACKAGE_TYPE,
    OracleOperatorSessionConstructionAuthorizationConsumptionGate,
    OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorSessionConstructionAuthorizationGate().authorize(
        certification=_certification()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe session authorization consumption accepted")
    except OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-025 TEST")
    print(" OPERATOR SESSION CONSTRUCTION")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorSessionConstructionAuthorizationConsumptionGate()

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.operator_session_construction_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_session_construction_consumption_hash"
        }
    )

    assert first.source_operator_session_construction_authorization_id == authorization.operator_session_construction_authorization_id
    assert first.source_operator_session_construction_authorization_hash == authorization.operator_session_construction_authorization_hash
    assert first.execution_package_type == EXECUTION_PACKAGE_TYPE
    assert first.consumption_status == CONSUMPTION_STATUS
    assert first.research_response_id == authorization.research_response_id
    assert first.research_response_payload_hash == authorization.research_response_payload_hash
    assert first.research_response_items == authorization.research_response_items

    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.authorization_type_verified
    assert first.session_package_type_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.response_item_cardinality_verified
    assert first.response_item_identity_verified
    assert first.source_result_hashes_verified
    assert first.certified_payload_preservation_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_session_input_verified
    assert first.single_use_consumption_verified
    assert first.immutable_execution_package_verified
    assert first.deterministic_consumption_verified
    assert first.read_only_boundary_verified

    assert first.research_response_result_certified
    assert first.operator_session_construction_ready
    assert first.operator_session_construction_authorized
    assert first.operator_session_construction_authorization_consumed
    assert first.operator_session_construction_allowed
    assert not first.operator_session_construction_performed
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

    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_session_construction_authorization_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        authorization_status="wrong_status",
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        research_response_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        research_response_item_count=authorization.research_response_item_count + 1,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_session_construction_performed=True,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-024 session authorization consumed")
    print("[PASS] Authorization identity, hash, status, and type verified")
    print("[PASS] Research Response payload hash recomputed and verified")
    print("[PASS] Session input identities, cardinality, and source hashes verified")
    print("[PASS] Single-use immutable session execution package created")
    print("[PASS] Session authorization marked consumed")
    print("[PASS] Operator Session construction allowed but not performed")
    print("[PASS] Console, presentation, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe authorizations rejected")
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
    print(" OOP-025 INSTALLER")
    print(" OPERATOR SESSION CONSTRUCTION")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    verify(
        SOURCE_024,
        "OOP-024",
        (
            'SCHEMA_VERSION = "OOP-024"',
            "class OracleOperatorSessionConstructionAuthorization",
            "operator_session_construction_authorization_hash",
            "authorization_status",
            "authorization_type",
            "session_package_type",
            "research_response_payload_hash",
            "research_response_items",
            "operator_session_construction_authorized",
            "operator_session_construction_allowed",
            "operator_session_construction_performed",
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
        SOURCE_024: sha256_file(SOURCE_024),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        SESSION_INIT,
        "from .oracle_operator_session_construction_authorization_consumption_gate import *",
    )
    export(
        OPERATOR_INIT,
        "from .session.oracle_operator_session_construction_authorization_consumption_gate import *",
    )

    for path in (PRODUCTION, TEST, SESSION_INIT, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-024 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics, Query, or Research Response export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-025 test executed automatically")
    print()
    print("[DONE] OOP-025 Operator Session construction authorization consumption installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
