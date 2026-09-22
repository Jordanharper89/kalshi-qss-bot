from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_gate import (
    CertifiedQueryResponseArtifactReadAuthorization,
)

SCHEMA_VERSION = "INT-OIA-046"
ENGINE_ID = "INT-OIA-046"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "read-authorization-consumption-gate.v1"
)
CONSUMPTION_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-read-authorization-consumption.v1"
)
CONSUMPTION_STATUS = (
    "certified_query_response_artifact_read_authorization_consumed"
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
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
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
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


def _verify_hash_record(
    value: Any,
    hash_field: str,
    label: str,
) -> None:
    body = asdict(value)
    supplied = body.pop(hash_field, None)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
        or stable_hash(body) != supplied
    ):
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactReadAuthorizationConsumption:
    consumption_id: str
    source_authorization_id: str
    source_authorization_hash: str
    source_read_result_id: str
    source_read_result_hash: str
    source_read_request_id: str
    source_read_request_hash: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    consuming_consumer_id: str
    consuming_projection: str
    consumed_entry_count: int
    consumed_response_artifact_entry_ids: tuple[str, ...]
    consumed_query_response_ids: tuple[str, ...]
    authorization_verified: bool
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    non_empty_authorization_verified: bool
    entry_identity_cardinality_verified: bool
    query_response_identity_cardinality_verified: bool
    single_use_verified: bool
    read_only_consumption_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_consumption_verified: bool
    authorization_consumed: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    consumption_status: str
    consumption_hash: str


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate:
    def __init__(self) -> None:
        self._consumed_authorization_ids: set[str] = set()

    @property
    def consumed_authorization_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._consumed_authorization_ids))

    @staticmethod
    def _verify_authorization(
        authorization: CertifiedQueryResponseArtifactReadAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            CertifiedQueryResponseArtifactReadAuthorization,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization must use the canonical INT-OIA-045 contract"
            )

        _verify_hash_record(
            authorization,
            "authorization_hash",
            "certified query response artifact read authorization",
        )

        if not authorization.authorization_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization identity is empty"
            )
        if authorization.authorized_entry_count < 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "empty authorization cannot be consumed"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_response_artifact_entry_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorized artifact-entry cardinality mismatch"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_query_response_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorized query-response cardinality mismatch"
            )
        if len(set(authorization.authorized_response_artifact_entry_ids)) != (
            authorization.authorized_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "duplicate authorized artifact-entry identity detected"
            )
        if len(set(authorization.authorized_query_response_ids)) != (
            authorization.authorized_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "duplicate authorized query-response identity detected"
            )

        if not (
            authorization.read_result_verified
            and authorization.registry_manifest_verified
            and authorization.registry_entry_hashes_verified
            and authorization.request_verified
            and authorization.non_empty_result_verified
            and authorization.single_consumer_verified
            and authorization.single_projection_verified
            and authorization.consumer_identity_verified
            and authorization.projection_identity_verified
            and authorization.immutable_read_verified
            and authorization.source_hashes_verified
            and authorization.lineage_verified
            and authorization.deterministic_ordering_verified
            and authorization.deterministic_replay_verified
            and authorization.read_authorized
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization is not eligible for consumption"
            )

        if (
            authorization.registry_mutation_allowed
            or authorization.registry_mutation_performed
            or authorization.publication_allowed
            or authorization.publication_performed
            or authorization.order_execution_allowed
            or authorization.order_execution_performed
            or authorization.database_connection_performed
            or authorization.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization contains forbidden activity"
            )

    def consume(
        self,
        *,
        authorization: CertifiedQueryResponseArtifactReadAuthorization,
        consuming_consumer_id: str,
        consuming_projection: str,
    ) -> CertifiedQueryResponseArtifactReadAuthorizationConsumption:
        self._verify_authorization(authorization)

        if (
            not isinstance(consuming_consumer_id, str)
            or not consuming_consumer_id.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "consuming_consumer_id must be a non-empty string"
            )
        if (
            not isinstance(consuming_projection, str)
            or not consuming_projection.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "consuming_projection must be a non-empty string"
            )
        if consuming_consumer_id != authorization.authorized_consumer_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "consuming consumer identity does not match authorization"
            )
        if consuming_projection != authorization.authorized_projection:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "consuming projection identity does not match authorization"
            )
        if authorization.authorization_id in self._consumed_authorization_ids:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization has already been consumed"
            )

        entry_ids = tuple(
            authorization.authorized_response_artifact_entry_ids
        )
        query_response_ids = tuple(
            authorization.authorized_query_response_ids
        )

        consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_authorization_id": authorization.authorization_id,
                "source_authorization_hash": authorization.authorization_hash,
                "consuming_consumer_id": consuming_consumer_id,
                "consuming_projection": consuming_projection,
                "consumed_response_artifact_entry_ids": entry_ids,
                "consumed_query_response_ids": query_response_ids,
            }
        )

        body = {
            "consumption_id": consumption_id,
            "source_authorization_id": authorization.authorization_id,
            "source_authorization_hash": authorization.authorization_hash,
            "source_read_result_id": authorization.source_read_result_id,
            "source_read_result_hash": authorization.source_read_result_hash,
            "source_read_request_id": authorization.source_read_request_id,
            "source_read_request_hash": authorization.source_read_request_hash,
            "source_registry_manifest_id": (
                authorization.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                authorization.source_registry_manifest_hash
            ),
            "consuming_consumer_id": consuming_consumer_id,
            "consuming_projection": consuming_projection,
            "consumed_entry_count": authorization.authorized_entry_count,
            "consumed_response_artifact_entry_ids": entry_ids,
            "consumed_query_response_ids": query_response_ids,
            "authorization_verified": True,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "non_empty_authorization_verified": True,
            "entry_identity_cardinality_verified": True,
            "query_response_identity_cardinality_verified": True,
            "single_use_verified": True,
            "read_only_consumption_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_consumption_verified": True,
            "authorization_consumed": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "consumption_status": CONSUMPTION_STATUS,
        }

        record = CertifiedQueryResponseArtifactReadAuthorizationConsumption(
            **body,
            consumption_hash=stable_hash(body),
        )
        self._consumed_authorization_ids.add(
            authorization.authorization_id
        )
        return record


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_SCHEMA_VERSION",
    "CONSUMPTION_STATUS",
    "CertifiedQueryResponseArtifactReadAuthorizationConsumption",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError",
    "stable_hash",
]
