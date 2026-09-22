from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import (
    AUTHORIZATION_SCHEMA_VERSION as INT_OIA_060_AUTHORIZATION_SCHEMA_VERSION,
    CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
)

SCHEMA_VERSION = "OOP-001"
ENGINE_ID = "OOP-001"
POLICY_ID = "oracle.operator.analytics-read-only-dependency-gate.v1"
DEPENDENCY_SCHEMA_VERSION = "oracle.operator.analytics-read-only-dependency-receipt.v1"
DEPENDENCY_STATUS = "int_oia_060_consumed_read_only"

EXPECTED_ANALYTICS_SCHEMA_VERSION = "INT-OIA-060"
EXPECTED_CONSUMER_ID = "oracle.operator.console.v1"
EXPECTED_PROJECTION = "operator_research"

OPERATOR_PACKAGE_NAMESPACE = "qseries_v2.oracle_operator"
ANALYTICS_PACKAGE_NAMESPACE = "qseries_v2.oracle_intelligence.analytics"
QSERIES_EXECUTION_PACKAGE_NAMESPACE = "qseries_v2.execution"


class OracleOperatorAnalyticsReadOnlyDependencyInvariantError(RuntimeError):
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
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
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


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _verify_int_oia_060_hash(
    authorization: CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
) -> None:
    body = asdict(authorization)
    supplied_hash = body.pop("authorization_hash", None)
    if not _valid_sha256(supplied_hash):
        raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
            "INT-OIA-060 authorization hash is not a canonical SHA-256 digest"
        )
    if stable_hash(body) != supplied_hash:
        raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
            "INT-OIA-060 authorization hash mismatch"
        )


@dataclass(frozen=True)
class OracleOperatorSubsystemBoundary:
    subsystem_id: str
    package_namespace: str
    query_namespace: str
    session_namespace: str
    console_namespace: str
    presentation_namespace: str
    analytics_namespace: str
    qseries_execution_namespace: str
    separate_from_analytics: bool
    separate_from_qseries_execution: bool
    analytics_mutation_allowed: bool
    qseries_execution_import_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    boundary_hash: str


@dataclass(frozen=True)
class OracleOperatorAnalyticsDependencyReceipt:
    dependency_receipt_id: str
    subsystem_boundary_hash: str
    source_schema_version: str
    source_authorization_schema_version: str
    source_authorization_id: str
    source_authorization_hash: str
    source_attestation_id: str
    source_attestation_hash: str
    source_consumption_id: str
    source_consumption_hash: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    authorized_consumer_id: str
    authorized_projection: str
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    source_type_verified: bool
    source_hash_verified: bool
    source_lineage_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    deterministic_replay_verified: bool
    read_only_dependency_verified: bool
    analytics_reexecution_performed: bool
    analytics_database_connection_performed: bool
    analytics_corpus_read_repeated: bool
    analytics_mutation_allowed: bool
    analytics_mutation_performed: bool
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
    dependency_status: str
    dependency_receipt_hash: str


class OracleOperatorAnalyticsReadOnlyDependencyGate:
    @staticmethod
    def subsystem_boundary() -> OracleOperatorSubsystemBoundary:
        body = {
            "subsystem_id": "oracle.operator",
            "package_namespace": OPERATOR_PACKAGE_NAMESPACE,
            "query_namespace": f"{OPERATOR_PACKAGE_NAMESPACE}.query",
            "session_namespace": f"{OPERATOR_PACKAGE_NAMESPACE}.session",
            "console_namespace": f"{OPERATOR_PACKAGE_NAMESPACE}.console",
            "presentation_namespace": f"{OPERATOR_PACKAGE_NAMESPACE}.presentation",
            "analytics_namespace": ANALYTICS_PACKAGE_NAMESPACE,
            "qseries_execution_namespace": QSERIES_EXECUTION_PACKAGE_NAMESPACE,
            "separate_from_analytics": True,
            "separate_from_qseries_execution": True,
            "analytics_mutation_allowed": False,
            "qseries_execution_import_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        return OracleOperatorSubsystemBoundary(
            **body,
            boundary_hash=stable_hash(body),
        )

    @staticmethod
    def _verify_source(
        authorization: CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
        ):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "dependency must use the canonical INT-OIA-060 authorization contract"
            )

        _verify_int_oia_060_hash(authorization)

        if not authorization.authorization_id:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization identity is empty"
            )
        if authorization.authorized_consumer_id != EXPECTED_CONSUMER_ID:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization is not for the Oracle Operator consumer"
            )
        if authorization.authorized_projection != EXPECTED_PROJECTION:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization projection is not operator_research"
            )
        if authorization.authorized_entry_count < 1:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization contains no entries"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_response_artifact_entry_ids
        ):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 artifact-entry cardinality mismatch"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_query_response_ids
        ):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 query-response cardinality mismatch"
            )
        if len(
            set(authorization.authorized_response_artifact_entry_ids)
        ) != authorization.authorized_entry_count:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "duplicate authorized artifact-entry identities detected"
            )
        if len(
            set(authorization.authorized_query_response_ids)
        ) != authorization.authorized_entry_count:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "duplicate authorized query-response identities detected"
            )

        required_truths = (
            authorization.attestation_hash_verified,
            authorization.attestation_identity_verified,
            authorization.consumption_lineage_verified,
            authorization.authorization_lineage_verified,
            authorization.prior_attestation_lineage_verified,
            authorization.prior_consumption_lineage_verified,
            authorization.prior_authorization_lineage_verified,
            authorization.read_authorization_lineage_verified,
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
            authorization.single_use_authorization_verified,
            authorization.read_only_consumption_verified,
            authorization.source_hashes_verified,
            authorization.lineage_verified,
            authorization.deterministic_ordering_verified,
            authorization.deterministic_consumption_verified,
            authorization.deterministic_replay_verified,
            authorization.attestation_authorized,
        )
        if not all(required_truths):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization is incomplete or uncertified"
            )

        forbidden_activity = (
            authorization.registry_mutation_allowed,
            authorization.registry_mutation_performed,
            authorization.publication_allowed,
            authorization.publication_performed,
            authorization.order_execution_allowed,
            authorization.order_execution_performed,
            authorization.database_connection_performed,
            authorization.corpus_read_execution_repeated,
        )
        if any(forbidden_activity):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization contains forbidden activity"
            )

    def consume(
        self,
        *,
        authorization: CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
    ) -> OracleOperatorAnalyticsDependencyReceipt:
        self._verify_source(authorization)
        boundary = self.subsystem_boundary()

        dependency_receipt_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "subsystem_boundary_hash": boundary.boundary_hash,
                "source_schema_version": EXPECTED_ANALYTICS_SCHEMA_VERSION,
                "source_authorization_id": authorization.authorization_id,
                "source_authorization_hash": authorization.authorization_hash,
                "authorized_consumer_id": authorization.authorized_consumer_id,
                "authorized_projection": authorization.authorized_projection,
                "authorized_response_artifact_entry_ids": (
                    authorization.authorized_response_artifact_entry_ids
                ),
                "authorized_query_response_ids": (
                    authorization.authorized_query_response_ids
                ),
            }
        )

        body = {
            "dependency_receipt_id": dependency_receipt_id,
            "subsystem_boundary_hash": boundary.boundary_hash,
            "source_schema_version": EXPECTED_ANALYTICS_SCHEMA_VERSION,
            "source_authorization_schema_version": (
                INT_OIA_060_AUTHORIZATION_SCHEMA_VERSION
            ),
            "source_authorization_id": authorization.authorization_id,
            "source_authorization_hash": authorization.authorization_hash,
            "source_attestation_id": authorization.source_attestation_id,
            "source_attestation_hash": authorization.source_attestation_hash,
            "source_consumption_id": authorization.source_consumption_id,
            "source_consumption_hash": authorization.source_consumption_hash,
            "source_registry_manifest_id": (
                authorization.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                authorization.source_registry_manifest_hash
            ),
            "authorized_consumer_id": authorization.authorized_consumer_id,
            "authorized_projection": authorization.authorized_projection,
            "authorized_entry_count": authorization.authorized_entry_count,
            "authorized_response_artifact_entry_ids": tuple(
                authorization.authorized_response_artifact_entry_ids
            ),
            "authorized_query_response_ids": tuple(
                authorization.authorized_query_response_ids
            ),
            "source_type_verified": True,
            "source_hash_verified": True,
            "source_lineage_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "deterministic_replay_verified": True,
            "read_only_dependency_verified": True,
            "analytics_reexecution_performed": False,
            "analytics_database_connection_performed": False,
            "analytics_corpus_read_repeated": False,
            "analytics_mutation_allowed": False,
            "analytics_mutation_performed": False,
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
            "dependency_status": DEPENDENCY_STATUS,
        }

        return OracleOperatorAnalyticsDependencyReceipt(
            **body,
            dependency_receipt_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "DEPENDENCY_SCHEMA_VERSION",
    "DEPENDENCY_STATUS",
    "EXPECTED_ANALYTICS_SCHEMA_VERSION",
    "EXPECTED_CONSUMER_ID",
    "EXPECTED_PROJECTION",
    "OPERATOR_PACKAGE_NAMESPACE",
    "ANALYTICS_PACKAGE_NAMESPACE",
    "QSERIES_EXECUTION_PACKAGE_NAMESPACE",
    "OracleOperatorSubsystemBoundary",
    "OracleOperatorAnalyticsDependencyReceipt",
    "OracleOperatorAnalyticsReadOnlyDependencyGate",
    "OracleOperatorAnalyticsReadOnlyDependencyInvariantError",
    "stable_hash",
]
