from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_consumption_gate import (
    CertifiedQueryResponseArtifactReadAuthorizationConsumption,
)

SCHEMA_VERSION = "INT-OIA-047"
ENGINE_ID = "INT-OIA-047"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "read-authorization-consumption-attestation-gate.v1"
)
ATTESTATION_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-read-authorization-"
    "consumption-attestation.v1"
)
ATTESTATION_STATUS = (
    "certified_query_response_artifact_read_authorization_"
    "consumption_independently_attested"
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
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
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
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
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestation:
    attestation_id: str
    source_consumption_id: str
    source_consumption_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_read_result_id: str
    source_read_result_hash: str
    source_read_request_id: str
    source_read_request_hash: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    attested_consumer_id: str
    attested_projection: str
    attested_entry_count: int
    attested_response_artifact_entry_ids: tuple[str, ...]
    attested_query_response_ids: tuple[str, ...]
    consumption_hash_verified: bool
    consumption_identity_verified: bool
    authorization_lineage_verified: bool
    read_result_lineage_verified: bool
    read_request_lineage_verified: bool
    registry_manifest_lineage_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    entry_identity_cardinality_verified: bool
    query_response_identity_cardinality_verified: bool
    unique_entry_identities_verified: bool
    unique_query_response_identities_verified: bool
    single_use_consumption_verified: bool
    read_only_consumption_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_consumption_verified: bool
    independent_attestation_verified: bool
    consumption_attested: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    attestation_status: str
    attestation_hash: str


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationGate:
    @staticmethod
    def _verify_consumption(
        consumption: CertifiedQueryResponseArtifactReadAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            CertifiedQueryResponseArtifactReadAuthorizationConsumption,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "consumption must use the canonical INT-OIA-046 contract"
            )

        _verify_hash_record(
            consumption,
            "consumption_hash",
            "read authorization consumption",
        )

        if not consumption.consumption_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "consumption identity is empty"
            )
        if not consumption.source_authorization_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "source authorization identity is empty"
            )
        if consumption.consumed_entry_count < 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "empty consumption cannot be attested"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_response_artifact_entry_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "consumed artifact-entry cardinality mismatch"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_query_response_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "consumed query-response cardinality mismatch"
            )
        if len(set(consumption.consumed_response_artifact_entry_ids)) != (
            consumption.consumed_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "duplicate consumed artifact-entry identity detected"
            )
        if len(set(consumption.consumed_query_response_ids)) != (
            consumption.consumed_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "duplicate consumed query-response identity detected"
            )

        if not (
            consumption.authorization_verified
            and consumption.authorization_identity_verified
            and consumption.authorization_hash_verified
            and consumption.consumer_identity_verified
            and consumption.projection_identity_verified
            and consumption.non_empty_authorization_verified
            and consumption.entry_identity_cardinality_verified
            and consumption.query_response_identity_cardinality_verified
            and consumption.single_use_verified
            and consumption.read_only_consumption_verified
            and consumption.source_hashes_verified
            and consumption.lineage_verified
            and consumption.deterministic_ordering_verified
            and consumption.deterministic_consumption_verified
            and consumption.authorization_consumed
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "consumption is not eligible for independent attestation"
            )

        if (
            consumption.registry_mutation_allowed
            or consumption.registry_mutation_performed
            or consumption.publication_allowed
            or consumption.publication_performed
            or consumption.order_execution_allowed
            or consumption.order_execution_performed
            or consumption.database_connection_performed
            or consumption.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError(
                "consumption contains forbidden activity"
            )

    def attest(
        self,
        *,
        consumption: CertifiedQueryResponseArtifactReadAuthorizationConsumption,
    ) -> CertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestation:
        self._verify_consumption(consumption)

        entry_ids = tuple(
            consumption.consumed_response_artifact_entry_ids
        )
        query_response_ids = tuple(
            consumption.consumed_query_response_ids
        )

        attestation_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.consumption_id,
                "source_consumption_hash": consumption.consumption_hash,
                "attested_consumer_id": consumption.consuming_consumer_id,
                "attested_projection": consumption.consuming_projection,
                "attested_response_artifact_entry_ids": entry_ids,
                "attested_query_response_ids": query_response_ids,
            }
        )

        body = {
            "attestation_id": attestation_id,
            "source_consumption_id": consumption.consumption_id,
            "source_consumption_hash": consumption.consumption_hash,
            "source_authorization_id": consumption.source_authorization_id,
            "source_authorization_hash": consumption.source_authorization_hash,
            "source_read_result_id": consumption.source_read_result_id,
            "source_read_result_hash": consumption.source_read_result_hash,
            "source_read_request_id": consumption.source_read_request_id,
            "source_read_request_hash": consumption.source_read_request_hash,
            "source_registry_manifest_id": (
                consumption.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                consumption.source_registry_manifest_hash
            ),
            "attested_consumer_id": consumption.consuming_consumer_id,
            "attested_projection": consumption.consuming_projection,
            "attested_entry_count": consumption.consumed_entry_count,
            "attested_response_artifact_entry_ids": entry_ids,
            "attested_query_response_ids": query_response_ids,
            "consumption_hash_verified": True,
            "consumption_identity_verified": True,
            "authorization_lineage_verified": True,
            "read_result_lineage_verified": True,
            "read_request_lineage_verified": True,
            "registry_manifest_lineage_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "entry_identity_cardinality_verified": True,
            "query_response_identity_cardinality_verified": True,
            "unique_entry_identities_verified": True,
            "unique_query_response_identities_verified": True,
            "single_use_consumption_verified": True,
            "read_only_consumption_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_consumption_verified": True,
            "independent_attestation_verified": True,
            "consumption_attested": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "attestation_status": ATTESTATION_STATUS,
        }

        return CertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestation(
            **body,
            attestation_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ATTESTATION_SCHEMA_VERSION",
    "ATTESTATION_STATUS",
    "CertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestation",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionAttestationInvariantError",
    "stable_hash",
]
