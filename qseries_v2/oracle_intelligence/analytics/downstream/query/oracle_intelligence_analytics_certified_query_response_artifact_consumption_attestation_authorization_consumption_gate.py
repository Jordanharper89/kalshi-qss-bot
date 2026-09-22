from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_gate import (
    CertifiedQueryResponseArtifactConsumptionAttestationAuthorization,
)

SCHEMA_VERSION = "INT-OIA-049"
ENGINE_ID = "INT-OIA-049"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "consumption-attestation-authorization-consumption-gate.v1"
)
CONSUMPTION_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-consumption-attestation-"
    "authorization-consumption.v1"
)
CONSUMPTION_STATUS = (
    "certified_query_response_artifact_consumption_attestation_"
    "authorization_consumed"
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
    RuntimeError
):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
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


def _verify_hash_record(value: Any, hash_field: str, label: str) -> None:
    body = asdict(value)
    supplied = body.pop(hash_field, None)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
        or stable_hash(body) != supplied
    ):
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumption:
    consumption_id: str
    source_authorization_id: str
    source_authorization_hash: str
    source_attestation_id: str
    source_attestation_hash: str
    source_consumption_id: str
    source_consumption_hash: str
    source_read_authorization_id: str
    source_read_authorization_hash: str
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
    authorization_hash_verified: bool
    authorization_identity_verified: bool
    attestation_lineage_verified: bool
    consumption_lineage_verified: bool
    read_authorization_lineage_verified: bool
    read_result_lineage_verified: bool
    read_request_lineage_verified: bool
    registry_manifest_lineage_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    entry_identity_cardinality_verified: bool
    query_response_identity_cardinality_verified: bool
    unique_entry_identities_verified: bool
    unique_query_response_identities_verified: bool
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


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionGate:
    def __init__(self) -> None:
        self._consumed_authorization_ids: set[str] = set()

    @property
    def consumed_authorization_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._consumed_authorization_ids))

    @staticmethod
    def _verify_authorization(
        authorization: CertifiedQueryResponseArtifactConsumptionAttestationAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            CertifiedQueryResponseArtifactConsumptionAttestationAuthorization,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "authorization must use the canonical INT-OIA-048 contract"
            )

        _verify_hash_record(
            authorization,
            "authorization_hash",
            "consumption attestation authorization",
        )

        if not authorization.authorization_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "authorization identity is empty"
            )
        if authorization.authorized_entry_count < 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "empty authorization cannot be consumed"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_response_artifact_entry_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "authorized artifact-entry cardinality mismatch"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_query_response_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "authorized query-response cardinality mismatch"
            )
        if len(set(authorization.authorized_response_artifact_entry_ids)) != (
            authorization.authorized_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "duplicate authorized artifact-entry identity detected"
            )
        if len(set(authorization.authorized_query_response_ids)) != (
            authorization.authorized_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "duplicate authorized query-response identity detected"
            )

        required = (
            authorization.attestation_hash_verified,
            authorization.attestation_identity_verified,
            authorization.consumption_lineage_verified,
            authorization.authorization_lineage_verified,
            authorization.read_result_lineage_verified,
            authorization.read_request_lineage_verified,
            authorization.registry_manifest_lineage_verified,
            authorization.consumer_identity_verified,
            authorization.projection_identity_verified,
            authorization.entry_identity_cardinality_verified,
            authorization.query_response_identity_cardinality_verified,
            authorization.unique_entry_identities_verified,
            authorization.unique_query_response_identities_verified,
            authorization.independent_attestation_verified,
            authorization.source_hashes_verified,
            authorization.lineage_verified,
            authorization.deterministic_ordering_verified,
            authorization.deterministic_replay_verified,
            authorization.attestation_authorized,
        )
        if not all(required):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
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
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "authorization contains forbidden activity"
            )

    def consume(
        self,
        *,
        authorization: CertifiedQueryResponseArtifactConsumptionAttestationAuthorization,
        consuming_consumer_id: str,
        consuming_projection: str,
    ) -> CertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumption:
        self._verify_authorization(authorization)

        if (
            not isinstance(consuming_consumer_id, str)
            or not consuming_consumer_id.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "consuming_consumer_id must be a non-empty string"
            )
        if (
            not isinstance(consuming_projection, str)
            or not consuming_projection.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "consuming_projection must be a non-empty string"
            )
        if consuming_consumer_id != authorization.authorized_consumer_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "consuming consumer does not match authorization"
            )
        if consuming_projection != authorization.authorized_projection:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
                "consuming projection does not match authorization"
            )
        if authorization.authorization_id in self._consumed_authorization_ids:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError(
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
            "source_attestation_id": authorization.source_attestation_id,
            "source_attestation_hash": authorization.source_attestation_hash,
            "source_consumption_id": authorization.source_consumption_id,
            "source_consumption_hash": authorization.source_consumption_hash,
            "source_read_authorization_id": (
                authorization.source_authorization_id
            ),
            "source_read_authorization_hash": (
                authorization.source_authorization_hash
            ),
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
            "authorization_hash_verified": True,
            "authorization_identity_verified": True,
            "attestation_lineage_verified": True,
            "consumption_lineage_verified": True,
            "read_authorization_lineage_verified": True,
            "read_result_lineage_verified": True,
            "read_request_lineage_verified": True,
            "registry_manifest_lineage_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "entry_identity_cardinality_verified": True,
            "query_response_identity_cardinality_verified": True,
            "unique_entry_identities_verified": True,
            "unique_query_response_identities_verified": True,
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

        record = CertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumption(
            **body,
            consumption_hash=stable_hash(body),
        )
        self._consumed_authorization_ids.add(authorization.authorization_id)
        return record


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_SCHEMA_VERSION",
    "CONSUMPTION_STATUS",
    "CertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumption",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionInvariantError",
    "stable_hash",
]
