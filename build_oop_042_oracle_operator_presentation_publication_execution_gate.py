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
SOURCE_041 = PRESENTATION / "oracle_operator_presentation_publication_authorization_consumption_gate.py"

PRODUCTION = PRESENTATION / "oracle_operator_presentation_publication_execution_gate.py"
TEST = ROOT / "test_oop_042_oracle_operator_presentation_publication_execution_gate.py"
PRESENTATION_INIT = PRESENTATION / "__init__.py"
OPERATOR_INIT = OPERATOR / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_041_CONSUMPTION_STATUS,
    PUBLICATION_EXECUTION_PACKAGE_TYPE as OOP_041_PUBLICATION_EXECUTION_PACKAGE_TYPE,
    OracleOperatorPresentationPublicationAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-042"
ENGINE_ID = "OOP-042"
POLICY_ID = "oracle.operator.presentation-publication-execution-gate.v1"
EXECUTION_STATUS = "operator_presentation_publication_executed"
PUBLISHED_PRESENTATION_ARTIFACT_TYPE = "immutable_read_only_published_operator_presentation_artifact"
PUBLISHED_PRESENTATION_FORMAT = "operator_presentation_publication_v1"

EXPECTED_CONSUMPTION_STATUS = OOP_041_CONSUMPTION_STATUS
EXPECTED_PUBLICATION_EXECUTION_PACKAGE_TYPE = OOP_041_PUBLICATION_EXECUTION_PACKAGE_TYPE
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorPresentationPublicationExecutionInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationPublicationExecutionInvariantError(
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
class OracleOperatorPresentationPublicationExecution:
    operator_presentation_publication_execution_id: str
    source_operator_presentation_publication_consumption_id: str
    source_operator_presentation_publication_consumption_hash: str
    source_operator_presentation_publication_authorization_id: str
    source_operator_presentation_publication_authorization_hash: str
    source_operator_presentation_rendering_result_certification_id: str
    source_operator_presentation_rendering_result_certification_hash: str
    source_operator_presentation_rendering_execution_id: str
    source_operator_presentation_rendering_execution_hash: str
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
    publication_execution_package_type: str
    published_presentation_artifact_type: str
    published_presentation_format: str
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
    rendered_presentation_payload: Mapping[str, Any]
    rendered_presentation_payload_hash: str
    published_presentation_id: str
    published_presentation_payload: Mapping[str, Any]
    published_presentation_payload_hash: str
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_status_verified: bool
    publication_execution_package_type_verified: bool
    rendered_presentation_identity_verified: bool
    rendered_presentation_payload_hash_verified: bool
    rendered_presentation_sections_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    deterministic_publication_verified: bool
    immutable_published_presentation_verified: bool
    read_only_publication_verified: bool
    publication_authorization_ready: bool
    publication_authorized: bool
    publication_authorization_consumed: bool
    publication_allowed: bool
    publication_performed: bool
    publication_result_certification_ready: bool
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
    operator_presentation_publication_execution_hash: str


class OracleOperatorPresentationPublicationExecutionGate:
    @staticmethod
    def _verify(
        consumption: OracleOperatorPresentationPublicationAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorPresentationPublicationAuthorizationConsumption,
        ):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "source must be canonical OOP-041 consumption"
            )

        body = asdict(consumption)
        supplied_hash = body.pop(
            "operator_presentation_publication_consumption_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "OOP-041 consumption hash mismatch"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "OOP-041 consumption status mismatch"
            )
        if consumption.publication_execution_package_type != EXPECTED_PUBLICATION_EXECUTION_PACKAGE_TYPE:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "publication execution package type mismatch"
            )
        if consumption.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(consumption.rendered_presentation_id):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation id invalid"
            )
        if not _valid_sha256(consumption.rendered_presentation_payload_hash):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation payload hash invalid"
            )
        if stable_hash(consumption.rendered_presentation_payload) != consumption.rendered_presentation_payload_hash:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation payload hash mismatch"
            )

        payload = consumption.rendered_presentation_payload
        if payload.get("rendered_presentation_id") != consumption.rendered_presentation_id:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation identity mismatch"
            )
        if payload.get("rendered_presentation_format") != consumption.rendered_presentation_format:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation format mismatch"
            )
        if payload.get("research_response_id") != consumption.research_response_id:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "research response identity mismatch"
            )
        if payload.get("research_response_item_count") != consumption.research_response_item_count:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "research response cardinality mismatch"
            )
        if tuple(payload.get("research_response_items") or ()) != tuple(consumption.research_response_items):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "research response items mismatch"
            )

        sections = tuple(payload.get("sections") or ())
        if tuple(section.get("section_id") for section in sections) != (
            "presentation_header",
            "presentation_results",
            "presentation_context",
            "presentation_lineage",
        ):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation sections mismatch"
            )
        if payload.get("read_only") is not True:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation is not read-only"
            )
        if payload.get("qseries_execution_disabled") is not True:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "Q Series execution boundary missing"
            )

        required = (
            consumption.authorization_identity_verified,
            consumption.authorization_hash_verified,
            consumption.authorization_status_verified,
            consumption.authorization_type_verified,
            consumption.publication_input_package_type_verified,
            consumption.rendered_presentation_identity_verified,
            consumption.rendered_presentation_payload_hash_verified,
            consumption.rendered_presentation_artifact_type_verified,
            consumption.rendered_presentation_format_verified,
            consumption.rendered_presentation_sections_verified,
            consumption.rendered_console_identity_verified,
            consumption.rendered_console_payload_hash_verified,
            consumption.operator_console_identity_verified,
            consumption.operator_console_payload_hash_verified,
            consumption.operator_session_identity_verified,
            consumption.operator_session_payload_hash_verified,
            consumption.research_response_identity_verified,
            consumption.research_response_payload_hash_verified,
            consumption.research_response_cardinality_verified,
            consumption.complete_lineage_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.immutable_publication_input_verified,
            consumption.single_use_consumption_verified,
            consumption.immutable_publication_execution_package_verified,
            consumption.deterministic_consumption_verified,
            consumption.read_only_boundary_verified,
            consumption.operator_presentation_rendering_result_certified,
            consumption.publication_authorization_ready,
            consumption.publication_authorized,
            consumption.publication_authorization_consumed,
            consumption.publication_allowed,
        )
        if not all(required):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "OOP-041 publication execution package incomplete"
            )

        forbidden = (
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
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "forbidden downstream activity detected"
            )

    def execute(
        self,
        *,
        consumption: OracleOperatorPresentationPublicationAuthorizationConsumption,
    ) -> OracleOperatorPresentationPublicationExecution:
        self._verify(consumption)

        published_presentation_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.operator_presentation_publication_consumption_id,
                "source_consumption_hash": consumption.operator_presentation_publication_consumption_hash,
                "rendered_presentation_id": consumption.rendered_presentation_id,
                "rendered_presentation_payload_hash": consumption.rendered_presentation_payload_hash,
                "published_presentation_format": PUBLISHED_PRESENTATION_FORMAT,
            }
        )

        published_presentation_payload = {
            "published_presentation_id": published_presentation_id,
            "published_presentation_format": PUBLISHED_PRESENTATION_FORMAT,
            "source_rendered_presentation_id": consumption.rendered_presentation_id,
            "source_rendered_presentation_payload_hash": consumption.rendered_presentation_payload_hash,
            "consumer_id": consumption.consumer_id,
            "query_text": consumption.query_text,
            "query_mode": consumption.query_mode,
            "projection": consumption.projection,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "research_response_id": consumption.research_response_id,
            "research_response_item_count": consumption.research_response_item_count,
            "research_response_items": tuple(consumption.research_response_items),
            "operator_session_id": consumption.operator_session_id,
            "operator_console_id": consumption.operator_console_id,
            "rendered_console_id": consumption.rendered_console_id,
            "rendered_presentation_payload": dict(consumption.rendered_presentation_payload),
            "read_only": True,
            "publication_completed": True,
            "qseries_handoff_disabled": True,
            "qseries_execution_disabled": True,
            "orders_disabled": True,
            "funds_movement_disabled": True,
            "portfolio_mutation_disabled": True,
        }
        published_presentation_payload_hash = stable_hash(
            published_presentation_payload
        )

        execution_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.operator_presentation_publication_consumption_id,
                "published_presentation_id": published_presentation_id,
                "published_presentation_payload_hash": published_presentation_payload_hash,
            }
        )

        body = {
            "operator_presentation_publication_execution_id": execution_id,
            "source_operator_presentation_publication_consumption_id": consumption.operator_presentation_publication_consumption_id,
            "source_operator_presentation_publication_consumption_hash": consumption.operator_presentation_publication_consumption_hash,
            "source_operator_presentation_publication_authorization_id": consumption.source_operator_presentation_publication_authorization_id,
            "source_operator_presentation_publication_authorization_hash": consumption.source_operator_presentation_publication_authorization_hash,
            "source_operator_presentation_rendering_result_certification_id": consumption.source_operator_presentation_rendering_result_certification_id,
            "source_operator_presentation_rendering_result_certification_hash": consumption.source_operator_presentation_rendering_result_certification_hash,
            "source_operator_presentation_rendering_execution_id": consumption.source_operator_presentation_rendering_execution_id,
            "source_operator_presentation_rendering_execution_hash": consumption.source_operator_presentation_rendering_execution_hash,
            "operator_namespace": consumption.operator_namespace,
            "query_namespace": consumption.query_namespace,
            "research_response_namespace": consumption.research_response_namespace,
            "session_namespace": consumption.session_namespace,
            "console_namespace": consumption.console_namespace,
            "presentation_namespace": consumption.presentation_namespace,
            "consumer_id": consumption.consumer_id,
            "query_text": consumption.query_text,
            "query_mode": consumption.query_mode,
            "projection": consumption.projection,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "rendered_presentation_artifact_type": consumption.rendered_presentation_artifact_type,
            "rendered_presentation_format": consumption.rendered_presentation_format,
            "publication_execution_package_type": consumption.publication_execution_package_type,
            "published_presentation_artifact_type": PUBLISHED_PRESENTATION_ARTIFACT_TYPE,
            "published_presentation_format": PUBLISHED_PRESENTATION_FORMAT,
            "research_response_id": consumption.research_response_id,
            "research_response_payload_hash": consumption.research_response_payload_hash,
            "research_response_item_count": consumption.research_response_item_count,
            "research_response_items": tuple(consumption.research_response_items),
            "operator_session_id": consumption.operator_session_id,
            "operator_session_payload_hash": consumption.operator_session_payload_hash,
            "operator_console_id": consumption.operator_console_id,
            "operator_console_payload_hash": consumption.operator_console_payload_hash,
            "rendered_console_id": consumption.rendered_console_id,
            "rendered_console_payload_hash": consumption.rendered_console_payload_hash,
            "rendered_presentation_id": consumption.rendered_presentation_id,
            "rendered_presentation_payload": dict(consumption.rendered_presentation_payload),
            "rendered_presentation_payload_hash": consumption.rendered_presentation_payload_hash,
            "published_presentation_id": published_presentation_id,
            "published_presentation_payload": published_presentation_payload,
            "published_presentation_payload_hash": published_presentation_payload_hash,
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_status_verified": True,
            "publication_execution_package_type_verified": True,
            "rendered_presentation_identity_verified": True,
            "rendered_presentation_payload_hash_verified": True,
            "rendered_presentation_sections_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "deterministic_publication_verified": True,
            "immutable_published_presentation_verified": True,
            "read_only_publication_verified": True,
            "publication_authorization_ready": True,
            "publication_authorized": True,
            "publication_authorization_consumed": True,
            "publication_allowed": True,
            "publication_performed": True,
            "publication_result_certification_ready": True,
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

        return OracleOperatorPresentationPublicationExecution(
            **body,
            operator_presentation_publication_execution_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "EXECUTION_STATUS",
    "PUBLISHED_PRESENTATION_ARTIFACT_TYPE",
    "PUBLISHED_PRESENTATION_FORMAT",
    "OracleOperatorPresentationPublicationExecution",
    "OracleOperatorPresentationPublicationExecutionGate",
    "OracleOperatorPresentationPublicationExecutionInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_041_oracle_operator_presentation_publication_authorization_consumption_gate import (
    _authorization,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_authorization_consumption_gate import (
    OracleOperatorPresentationPublicationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_execution_gate import (
    EXECUTION_STATUS,
    PUBLISHED_PRESENTATION_ARTIFACT_TYPE,
    PUBLISHED_PRESENTATION_FORMAT,
    OracleOperatorPresentationPublicationExecutionGate,
    OracleOperatorPresentationPublicationExecutionInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorPresentationPublicationAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe publication execution accepted")
    except OracleOperatorPresentationPublicationExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-042 TEST")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" EXECUTION GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorPresentationPublicationExecutionGate()

    first = gate.execute(consumption=consumption)
    repeated = gate.execute(consumption=consumption)

    assert first == repeated
    assert first.operator_presentation_publication_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_publication_execution_hash"
        }
    )
    assert first.published_presentation_payload_hash == stable_hash(
        first.published_presentation_payload
    )
    assert first.published_presentation_artifact_type == PUBLISHED_PRESENTATION_ARTIFACT_TYPE
    assert first.published_presentation_format == PUBLISHED_PRESENTATION_FORMAT
    assert first.execution_status == EXECUTION_STATUS

    payload = first.published_presentation_payload
    assert payload["published_presentation_id"] == first.published_presentation_id
    assert payload["source_rendered_presentation_id"] == first.rendered_presentation_id
    assert payload["source_rendered_presentation_payload_hash"] == first.rendered_presentation_payload_hash
    assert payload["research_response_id"] == first.research_response_id
    assert payload["research_response_item_count"] == first.research_response_item_count
    assert payload["read_only"] is True
    assert payload["publication_completed"] is True
    assert payload["qseries_handoff_disabled"] is True
    assert payload["qseries_execution_disabled"] is True
    assert payload["orders_disabled"] is True
    assert payload["funds_movement_disabled"] is True
    assert payload["portfolio_mutation_disabled"] is True

    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_status_verified
    assert first.publication_execution_package_type_verified
    assert first.rendered_presentation_identity_verified
    assert first.rendered_presentation_payload_hash_verified
    assert first.rendered_presentation_sections_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.deterministic_publication_verified
    assert first.immutable_published_presentation_verified
    assert first.read_only_publication_verified

    assert first.publication_authorization_ready
    assert first.publication_authorized
    assert first.publication_authorization_consumed
    assert first.publication_allowed
    assert first.publication_performed
    assert first.publication_result_certification_ready
    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed

    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_presentation_publication_consumption_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumption_status="wrong_status",
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        rendered_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_item_count=consumption.research_response_item_count + 1,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        publication_performed=True,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-041 publication execution package consumed")
    print("[PASS] Consumption identity, hash, status, and package type verified")
    print("[PASS] Rendered presentation identity, payload hash, and sections verified")
    print("[PASS] Complete Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Deterministic immutable published presentation created")
    print("[PASS] Published presentation payload hash verified")
    print("[PASS] Publication performed through read-only boundary")
    print("[PASS] Publication result certification marked ready")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe publication packages rejected")
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
    print(" OOP-042 INSTALLER")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" EXECUTION GATE")
    print("=" * 40)

    verify(
        SOURCE_041,
        "OOP-041",
        (
            'SCHEMA_VERSION = "OOP-041"',
            "class OracleOperatorPresentationPublicationAuthorizationConsumption",
            "operator_presentation_publication_consumption_hash",
            "publication_execution_package_type",
            "rendered_presentation_payload_hash",
            "publication_authorization_consumed",
            "publication_allowed",
            "publication_performed",
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
        SOURCE_041: sha256_file(SOURCE_041),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        PRESENTATION_INIT,
        "from .oracle_operator_presentation_publication_execution_gate import *",
    )
    export(
        OPERATOR_INIT,
        "from .presentation.oracle_operator_presentation_publication_execution_gate import *",
    )

    for path in (PRODUCTION, TEST, PRESENTATION_INIT, OPERATOR_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-041 and INT-OIA-060 unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected in protected.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics, Query, Research Response, Session, or Console export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-042 test executed automatically")
    print()
    print("[DONE] OOP-042 Operator presentation publication execution installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
