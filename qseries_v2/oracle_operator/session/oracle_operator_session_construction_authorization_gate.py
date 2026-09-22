from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_result_certification_gate import (
    CERTIFICATION_STATUS as OOP_023_CERTIFICATION_STATUS,
    CERTIFICATION_TYPE as OOP_023_CERTIFICATION_TYPE,
    OracleOperatorResearchResponseMaterializationResultCertification,
)

SCHEMA_VERSION = "OOP-024"
ENGINE_ID = "OOP-024"
POLICY_ID = "oracle.operator.session-construction-authorization-gate.v1"
AUTHORIZATION_STATUS = "operator_session_construction_authorized"
AUTHORIZATION_TYPE = "single_use_immutable_operator_session_construction_authorization"
SESSION_PACKAGE_TYPE = "certified_operator_session_construction_input_package"

EXPECTED_CERTIFICATION_STATUS = OOP_023_CERTIFICATION_STATUS
EXPECTED_CERTIFICATION_TYPE = OOP_023_CERTIFICATION_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"
EXPECTED_SESSION_NAMESPACE = "qseries_v2.oracle_operator.session"


class OracleOperatorSessionConstructionAuthorizationInvariantError(RuntimeError):
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
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorSessionConstructionAuthorizationInvariantError(
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
class OracleOperatorSessionConstructionAuthorization:
    operator_session_construction_authorization_id: str
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
    certification_identity_verified: bool
    certification_hash_verified: bool
    certification_status_verified: bool
    certification_type_verified: bool
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
    single_use_authorization_verified: bool
    deterministic_authorization_verified: bool
    read_only_boundary_verified: bool
    query_subsystem_complete: bool
    research_response_result_certified: bool
    operator_session_construction_ready: bool
    operator_session_construction_authorized: bool
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
    authorization_status: str
    operator_session_construction_authorization_hash: str


class OracleOperatorSessionConstructionAuthorizationGate:
    @staticmethod
    def _verify(
        certification: OracleOperatorResearchResponseMaterializationResultCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorResearchResponseMaterializationResultCertification,
        ):
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "source must be canonical OOP-023 certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop(
            "research_response_materialization_result_certification_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "OOP-023 certification hash mismatch"
            )

        if certification.certification_status != EXPECTED_CERTIFICATION_STATUS:
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "OOP-023 certification status mismatch"
            )
        if certification.certification_type != EXPECTED_CERTIFICATION_TYPE:
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "OOP-023 certification type mismatch"
            )
        if certification.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "operator namespace mismatch"
            )
        if certification.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "query namespace mismatch"
            )
        if certification.research_response_namespace != EXPECTED_RESEARCH_RESPONSE_NAMESPACE:
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "research response namespace mismatch"
            )

        if not _valid_sha256(certification.research_response_id):
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "research response id invalid"
            )
        if not _valid_sha256(certification.research_response_payload_hash):
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "research response payload hash invalid"
            )
        if stable_hash(certification.research_response_payload) != certification.research_response_payload_hash:
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "research response payload hash mismatch"
            )

        count = certification.research_response_item_count
        if count < 1:
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "certification contains no response items"
            )
        if not (
            count == len(certification.research_response_items)
            == certification.source_entry_count
            == certification.source_result_count
            == len(certification.source_response_artifact_entry_ids)
            == len(certification.source_query_response_ids)
            == len(certification.source_result_hashes)
        ):
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "certification cardinality mismatch"
            )

        for index, item in enumerate(certification.research_response_items):
            if item.get("ordinal") != index + 1:
                raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                    "response item ordinal mismatch"
                )
            if item.get("response_artifact_entry_id") != certification.source_response_artifact_entry_ids[index]:
                raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                    "artifact entry identity mismatch"
                )
            if item.get("query_response_id") != certification.source_query_response_ids[index]:
                raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                    "query response identity mismatch"
                )
            if item.get("source_result_hash") != certification.source_result_hashes[index]:
                raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                    "source result identity mismatch"
                )
            certified_payload = item.get("certified_payload")
            if not isinstance(certified_payload, Mapping):
                raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                    "certified payload missing"
                )
            if stable_hash(certified_payload) != certification.source_result_hashes[index]:
                raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                    "certified payload hash mismatch"
                )

        required = (
            certification.execution_identity_verified,
            certification.execution_hash_verified,
            certification.execution_status_verified,
            certification.response_identity_verified,
            certification.response_payload_hash_verified,
            certification.response_format_verified,
            certification.response_artifact_type_verified,
            certification.response_item_cardinality_verified,
            certification.response_item_identity_verified,
            certification.source_result_hashes_verified,
            certification.certified_payload_preservation_verified,
            certification.read_only_response_verified,
            certification.immutable_response_verified,
            certification.deterministic_certification_verified,
            certification.complete_lineage_verified,
            certification.frozen_scope_verified,
            certification.frozen_scope_preserved,
            certification.query_subsystem_complete,
            certification.research_response_result_certified,
            certification.operator_session_construction_ready,
        )
        if not all(required):
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "OOP-023 certification incomplete"
            )

        forbidden = (
            certification.operator_session_construction_allowed,
            certification.operator_console_rendering_allowed,
            certification.operator_presentation_rendering_allowed,
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
            raise OracleOperatorSessionConstructionAuthorizationInvariantError(
                "forbidden downstream activity detected"
            )

    def authorize(
        self,
        *,
        certification: OracleOperatorResearchResponseMaterializationResultCertification,
    ) -> OracleOperatorSessionConstructionAuthorization:
        self._verify(certification)

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_certification_id": certification.research_response_materialization_result_certification_id,
                "source_certification_hash": certification.research_response_materialization_result_certification_hash,
                "research_response_id": certification.research_response_id,
                "research_response_payload_hash": certification.research_response_payload_hash,
                "authorization_type": AUTHORIZATION_TYPE,
                "session_package_type": SESSION_PACKAGE_TYPE,
            }
        )

        body = {
            "operator_session_construction_authorization_id": authorization_id,
            "source_research_response_result_certification_id": certification.research_response_materialization_result_certification_id,
            "source_research_response_result_certification_hash": certification.research_response_materialization_result_certification_hash,
            "source_research_response_materialization_execution_id": certification.source_research_response_materialization_execution_id,
            "source_research_response_materialization_execution_hash": certification.source_research_response_materialization_execution_hash,
            "source_research_response_materialization_consumption_id": certification.source_research_response_materialization_consumption_id,
            "source_research_response_materialization_consumption_hash": certification.source_research_response_materialization_consumption_hash,
            "operator_namespace": certification.operator_namespace,
            "query_namespace": certification.query_namespace,
            "research_response_namespace": certification.research_response_namespace,
            "session_namespace": EXPECTED_SESSION_NAMESPACE,
            "consumer_id": certification.consumer_id,
            "projection": certification.projection,
            "query_mode": certification.query_mode,
            "query_text": certification.query_text,
            "time_scope": certification.time_scope,
            "sort_order": certification.sort_order,
            "result_limit": certification.result_limit,
            "requested_tags": tuple(certification.requested_tags),
            "research_response_artifact_type": certification.research_response_artifact_type,
            "response_format": certification.response_format,
            "certification_type": certification.certification_type,
            "authorization_type": AUTHORIZATION_TYPE,
            "session_package_type": SESSION_PACKAGE_TYPE,
            "source_entry_count": certification.source_entry_count,
            "source_response_artifact_entry_ids": tuple(certification.source_response_artifact_entry_ids),
            "source_query_response_ids": tuple(certification.source_query_response_ids),
            "source_result_count": certification.source_result_count,
            "source_result_hashes": tuple(certification.source_result_hashes),
            "research_response_id": certification.research_response_id,
            "research_response_item_count": certification.research_response_item_count,
            "research_response_items": tuple(certification.research_response_items),
            "research_response_payload": dict(certification.research_response_payload),
            "research_response_payload_hash": certification.research_response_payload_hash,
            "certification_identity_verified": True,
            "certification_hash_verified": True,
            "certification_status_verified": True,
            "certification_type_verified": True,
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
            "single_use_authorization_verified": True,
            "deterministic_authorization_verified": True,
            "read_only_boundary_verified": True,
            "query_subsystem_complete": True,
            "research_response_result_certified": True,
            "operator_session_construction_ready": True,
            "operator_session_construction_authorized": True,
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
            "authorization_status": AUTHORIZATION_STATUS,
        }

        return OracleOperatorSessionConstructionAuthorization(
            **body,
            operator_session_construction_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_STATUS",
    "AUTHORIZATION_TYPE",
    "SESSION_PACKAGE_TYPE",
    "OracleOperatorSessionConstructionAuthorization",
    "OracleOperatorSessionConstructionAuthorizationGate",
    "OracleOperatorSessionConstructionAuthorizationInvariantError",
    "stable_hash",
]
