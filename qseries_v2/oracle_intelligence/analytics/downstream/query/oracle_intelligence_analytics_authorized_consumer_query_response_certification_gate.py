from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_registry_query_execution_gate import (
    AuthorizedConsumerRegistryQueryExecutionRecord,
)

SCHEMA_VERSION = "INT-OIA-042"
ENGINE_ID = "INT-OIA-042"
POLICY_ID = (
    "oracle.intelligence.analytics.authorized-consumer-query-response."
    "certification-gate.v1"
)
QUERY_RESPONSE_SCHEMA_VERSION = (
    "oracle.authorized-consumer-query-response-certification.v1"
)
QUERY_RESPONSE_STATUS = "authorized_consumer_query_response_certified"

ALLOWED_PROJECTIONS = (
    "operator_research",
    "research_presentation",
    "audit_replay",
)

COMMON_RESPONSE_FIELDS = (
    "intelligence_product_id",
    "product_type",
    "market_id",
    "venue_id",
    "confidence",
    "calibration_status",
    "product_state",
    "registry_entry_hash",
)

PROJECTION_RESPONSE_FIELDS: dict[str, tuple[str, ...]] = {
    "operator_research": COMMON_RESPONSE_FIELDS + (
        "registry_key",
        "query_eligible",
        "projection_eligible",
        "source_hashes_verified",
        "lineage_verified",
    ),
    "research_presentation": COMMON_RESPONSE_FIELDS + (
        "query_eligible",
        "projection_eligible",
    ),
    "audit_replay": (
        "sequence",
        "registry_entry_id",
        "product_admission_id",
        "product_admission_record_hash",
        "intelligence_product_id",
        "intelligence_product_hash",
        "source_canonical_product_manifest_id",
        "source_canonical_product_manifest_hash",
        "source_product_admission_manifest_id",
        "source_product_admission_manifest_hash",
        "source_result_admission_id",
        "source_result_admission_record_hash",
        "product_schema_version",
        "product_class",
        "product_type",
        "product_mode",
        "product_state",
        "market_id",
        "venue_id",
        "confidence",
        "calibration_status",
        "allowed_consumer_projections",
        "registry_partition",
        "registry_key",
        "immutable",
        "read_only",
        "deterministic",
        "replayable",
        "query_eligible",
        "projection_eligible",
        "publication_eligible",
        "publication_performed",
        "execution_capabilities_disabled_verified",
        "source_hashes_verified",
        "lineage_verified",
        "admission_verified",
        "duplicate_registration_rejected",
        "registry_entry_status",
        "registry_entry_hash",
    ),
}

FORBIDDEN_RESPONSE_FIELDS = (
    "database_url",
    "database_password",
    "api_key",
    "secret",
    "private_key",
    "order_payload",
    "execution_payload",
    "mutation_payload",
)


class OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
    RuntimeError
):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
        f"unsupported non-deterministic value type: {type(value)!r}"
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


def _verify_record_hash(record: AuthorizedConsumerRegistryQueryExecutionRecord) -> None:
    body = asdict(record)
    supplied = body.pop("query_execution_record_hash", None)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
        or stable_hash(body) != supplied
    ):
        raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
            "query execution record hash mismatch"
        )


def _contains_forbidden_field(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = str(key).lower()
            if any(token in normalized_key for token in FORBIDDEN_RESPONSE_FIELDS):
                return True
            if _contains_forbidden_field(item):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_field(item) for item in value)
    return False


@dataclass(frozen=True)
class CertifiedConsumerQueryResponseItem:
    sequence: int
    projected_entry: dict[str, Any]
    projected_entry_hash: str


@dataclass(frozen=True)
class CertifiedConsumerQueryResponseRecord:
    query_response_id: str
    source_query_execution_id: str
    source_query_execution_record_hash: str
    source_query_admission_id: str
    source_request_id: str
    consumer_id: str
    requested_projection: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    source_read_result_hash: str
    matched_entry_count: int
    certified_response_item_count: int
    certified_response_items: tuple[CertifiedConsumerQueryResponseItem, ...]
    source_execution_verified: bool
    projection_policy_verified: bool
    field_allowlist_enforced: bool
    forbidden_fields_absent: bool
    response_item_hashes_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_replay_verified: bool
    immutable_read_verified: bool
    response_artifact_persistence_allowed: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    query_response_status: str
    query_response_record_hash: str


class OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationGate:
    @staticmethod
    def _verify_execution(
        execution: AuthorizedConsumerRegistryQueryExecutionRecord,
    ) -> None:
        if not isinstance(
            execution,
            AuthorizedConsumerRegistryQueryExecutionRecord,
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution must use the canonical INT-OIA-041 record contract"
            )

        _verify_record_hash(execution)

        if execution.source_requested_projection not in ALLOWED_PROJECTIONS:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution requested an unsupported response projection"
            )

        if not (
            execution.query_admission_verified
            and execution.registry_read_request_derived_from_admission
            and execution.registry_read_invocation_count == 1
            and execution.registry_read_result_verified
            and execution.source_hashes_verified
            and execution.lineage_verified
            and execution.deterministic_replay_verified
            and execution.immutable_read_verified
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution is not eligible for response certification"
            )

        if execution.matched_entry_count != len(
            execution.matched_registry_entries
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution matched-entry count mismatch"
            )

        if (
            execution.registry_mutation_allowed
            or execution.registry_mutation_performed
            or execution.registry_update_performed
            or execution.registry_delete_performed
            or execution.publication_allowed
            or execution.publication_performed
            or execution.order_execution_allowed
            or execution.order_execution_performed
            or execution.database_connection_performed
            or execution.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "query execution contains unsafe activity"
            )

    @staticmethod
    def _project_entry(
        entry: Mapping[str, Any],
        projection: str,
    ) -> dict[str, Any]:
        if not isinstance(entry, Mapping):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "registry entry must be a mapping"
            )

        allowed_fields = PROJECTION_RESPONSE_FIELDS[projection]
        missing = [
            field_name
            for field_name in COMMON_RESPONSE_FIELDS
            if field_name not in entry
        ]
        if missing:
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "registry entry missing required response fields: "
                + ", ".join(missing)
            )

        projected = {
            field_name: _canonical(entry[field_name])
            for field_name in allowed_fields
            if field_name in entry
        }

        if _contains_forbidden_field(projected):
            raise OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError(
                "projected response contains forbidden fields"
            )

        return projected

    def certify(
        self,
        execution: AuthorizedConsumerRegistryQueryExecutionRecord,
    ) -> CertifiedConsumerQueryResponseRecord:
        self._verify_execution(execution)

        projection = execution.source_requested_projection
        projected_items: list[CertifiedConsumerQueryResponseItem] = []

        for index, entry in enumerate(
            execution.matched_registry_entries,
            start=1,
        ):
            projected_entry = self._project_entry(entry, projection)
            projected_items.append(
                CertifiedConsumerQueryResponseItem(
                    sequence=index,
                    projected_entry=projected_entry,
                    projected_entry_hash=stable_hash(projected_entry),
                )
            )

        response_items = tuple(projected_items)

        query_response_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_query_execution_id": execution.query_execution_id,
                "source_query_execution_record_hash": (
                    execution.query_execution_record_hash
                ),
                "consumer_id": execution.source_consumer_id,
                "requested_projection": projection,
                "response_item_hashes": [
                    item.projected_entry_hash for item in response_items
                ],
            }
        )

        body = {
            "query_response_id": query_response_id,
            "source_query_execution_id": execution.query_execution_id,
            "source_query_execution_record_hash": (
                execution.query_execution_record_hash
            ),
            "source_query_admission_id": (
                execution.source_query_admission_id
            ),
            "source_request_id": execution.source_request_id,
            "consumer_id": execution.source_consumer_id,
            "requested_projection": projection,
            "source_registry_manifest_id": (
                execution.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                execution.source_registry_manifest_hash
            ),
            "source_read_result_hash": execution.source_read_result_hash,
            "matched_entry_count": execution.matched_entry_count,
            "certified_response_item_count": len(response_items),
            "certified_response_items": response_items,
            "source_execution_verified": True,
            "projection_policy_verified": True,
            "field_allowlist_enforced": True,
            "forbidden_fields_absent": True,
            "response_item_hashes_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_replay_verified": True,
            "immutable_read_verified": True,
            "response_artifact_persistence_allowed": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "query_response_status": QUERY_RESPONSE_STATUS,
        }

        return CertifiedConsumerQueryResponseRecord(
            **body,
            query_response_record_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "QUERY_RESPONSE_SCHEMA_VERSION",
    "QUERY_RESPONSE_STATUS",
    "ALLOWED_PROJECTIONS",
    "PROJECTION_RESPONSE_FIELDS",
    "CertifiedConsumerQueryResponseItem",
    "CertifiedConsumerQueryResponseRecord",
    "OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationGate",
    "OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError",
    "stable_hash",
]
