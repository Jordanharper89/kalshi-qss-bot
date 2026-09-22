from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_consumption_authorization_consumption_attestation_gate import (
    CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestation,
)

SCHEMA_VERSION = "INT-OIA-051"
ENGINE_ID = "INT-OIA-051"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "consumption-authorization-consumption-attestation-authorization-gate.v1"
)
AUTHORIZATION_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-consumption-authorization-"
    "consumption-attestation-authorization.v1"
)
AUTHORIZATION_STATUS = (
    "certified_query_response_artifact_consumption_authorization_"
    "consumption_attestation_authorized"
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
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
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
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
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorization:
    authorization_id: str
    source_attestation_id: str
    source_attestation_hash: str
    source_consumption_id: str
    source_consumption_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_prior_attestation_id: str
    source_prior_attestation_hash: str
    source_prior_consumption_id: str
    source_prior_consumption_hash: str
    source_read_authorization_id: str
    source_read_authorization_hash: str
    source_read_result_id: str
    source_read_result_hash: str
    source_read_request_id: str
    source_read_request_hash: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    authorized_consumer_id: str
    authorized_projection: str
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    attestation_hash_verified: bool
    attestation_identity_verified: bool
    consumption_lineage_verified: bool
    authorization_lineage_verified: bool
    prior_attestation_lineage_verified: bool
    prior_consumption_lineage_verified: bool
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
    independent_attestation_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_replay_verified: bool
    attestation_authorized: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    authorization_status: str
    authorization_hash: str


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationGate:
    @staticmethod
    def _verify_attestation(
        attestation: CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestation,
    ) -> None:
        if not isinstance(
            attestation,
            CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestation,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attestation must use the canonical INT-OIA-050 contract"
            )

        _verify_hash_record(
            attestation,
            "attestation_hash",
            "authorization consumption attestation",
        )

        if not attestation.attestation_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attestation identity is empty"
            )
        if attestation.attested_entry_count < 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "empty attestation cannot be authorized"
            )
        if attestation.attested_entry_count != len(
            attestation.attested_response_artifact_entry_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attested artifact-entry cardinality mismatch"
            )
        if attestation.attested_entry_count != len(
            attestation.attested_query_response_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attested query-response cardinality mismatch"
            )
        if len(set(attestation.attested_response_artifact_entry_ids)) != (
            attestation.attested_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "duplicate attested artifact-entry identity detected"
            )
        if len(set(attestation.attested_query_response_ids)) != (
            attestation.attested_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "duplicate attested query-response identity detected"
            )

        required = (
            attestation.consumption_hash_verified,
            attestation.consumption_identity_verified,
            attestation.authorization_lineage_verified,
            attestation.attestation_lineage_verified,
            attestation.prior_consumption_lineage_verified,
            attestation.read_authorization_lineage_verified,
            attestation.read_result_lineage_verified,
            attestation.read_request_lineage_verified,
            attestation.registry_manifest_lineage_verified,
            attestation.consumer_identity_verified,
            attestation.projection_identity_verified,
            attestation.entry_identity_cardinality_verified,
            attestation.query_response_identity_cardinality_verified,
            attestation.unique_entry_identities_verified,
            attestation.unique_query_response_identities_verified,
            attestation.single_use_consumption_verified,
            attestation.read_only_consumption_verified,
            attestation.source_hashes_verified,
            attestation.lineage_verified,
            attestation.deterministic_ordering_verified,
            attestation.deterministic_consumption_verified,
            attestation.independent_attestation_verified,
            attestation.consumption_attested,
        )
        if not all(required):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attestation is not eligible for authorization"
            )

        if (
            attestation.registry_mutation_allowed
            or attestation.registry_mutation_performed
            or attestation.publication_allowed
            or attestation.publication_performed
            or attestation.order_execution_allowed
            or attestation.order_execution_performed
            or attestation.database_connection_performed
            or attestation.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attestation contains forbidden activity"
            )

    def authorize(
        self,
        *,
        attestation: CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestation,
        authorized_consumer_id: str,
        authorized_projection: str,
    ) -> CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorization:
        self._verify_attestation(attestation)

        if (
            not isinstance(authorized_consumer_id, str)
            or not authorized_consumer_id.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "authorized_consumer_id must be a non-empty string"
            )
        if (
            not isinstance(authorized_projection, str)
            or not authorized_projection.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "authorized_projection must be a non-empty string"
            )
        if authorized_consumer_id != attestation.attested_consumer_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "authorized consumer does not match attested consumer"
            )
        if authorized_projection != attestation.attested_projection:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "authorized projection does not match attested projection"
            )

        entry_ids = tuple(attestation.attested_response_artifact_entry_ids)
        query_response_ids = tuple(attestation.attested_query_response_ids)

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_attestation_id": attestation.attestation_id,
                "source_attestation_hash": attestation.attestation_hash,
                "authorized_consumer_id": authorized_consumer_id,
                "authorized_projection": authorized_projection,
                "authorized_response_artifact_entry_ids": entry_ids,
                "authorized_query_response_ids": query_response_ids,
            }
        )

        body = {
            "authorization_id": authorization_id,
            "source_attestation_id": attestation.attestation_id,
            "source_attestation_hash": attestation.attestation_hash,
            "source_consumption_id": attestation.source_consumption_id,
            "source_consumption_hash": attestation.source_consumption_hash,
            "source_authorization_id": attestation.source_authorization_id,
            "source_authorization_hash": attestation.source_authorization_hash,
            "source_prior_attestation_id": attestation.source_attestation_id,
            "source_prior_attestation_hash": attestation.source_attestation_hash,
            "source_prior_consumption_id": (
                attestation.source_prior_consumption_id
            ),
            "source_prior_consumption_hash": (
                attestation.source_prior_consumption_hash
            ),
            "source_read_authorization_id": (
                attestation.source_read_authorization_id
            ),
            "source_read_authorization_hash": (
                attestation.source_read_authorization_hash
            ),
            "source_read_result_id": attestation.source_read_result_id,
            "source_read_result_hash": attestation.source_read_result_hash,
            "source_read_request_id": attestation.source_read_request_id,
            "source_read_request_hash": attestation.source_read_request_hash,
            "source_registry_manifest_id": (
                attestation.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                attestation.source_registry_manifest_hash
            ),
            "authorized_consumer_id": authorized_consumer_id,
            "authorized_projection": authorized_projection,
            "authorized_entry_count": attestation.attested_entry_count,
            "authorized_response_artifact_entry_ids": entry_ids,
            "authorized_query_response_ids": query_response_ids,
            "attestation_hash_verified": True,
            "attestation_identity_verified": True,
            "consumption_lineage_verified": True,
            "authorization_lineage_verified": True,
            "prior_attestation_lineage_verified": True,
            "prior_consumption_lineage_verified": True,
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
            "independent_attestation_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_replay_verified": True,
            "attestation_authorized": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "authorization_status": AUTHORIZATION_STATUS,
        }

        return CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorization(
            **body,
            authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_SCHEMA_VERSION",
    "AUTHORIZATION_STATUS",
    "CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorization",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationAuthorizationInvariantError",
    "stable_hash",
]
