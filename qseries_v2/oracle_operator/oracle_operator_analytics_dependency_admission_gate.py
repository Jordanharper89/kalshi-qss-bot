from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.oracle_operator_analytics_read_only_dependency_gate import (
    DEPENDENCY_STATUS as OOP_001_DEPENDENCY_STATUS,
    EXPECTED_ANALYTICS_SCHEMA_VERSION,
    EXPECTED_CONSUMER_ID,
    EXPECTED_PROJECTION,
    INT_OIA_060_AUTHORIZATION_SCHEMA_VERSION,
    OPERATOR_PACKAGE_NAMESPACE,
    OracleOperatorAnalyticsDependencyReceipt,
)

SCHEMA_VERSION = "OOP-002"
ENGINE_ID = "OOP-002"
POLICY_ID = "oracle.operator.analytics-dependency-admission-gate.v1"
ADMISSION_SCHEMA_VERSION = "oracle.operator.analytics-dependency-admission.v1"
ADMISSION_STATUS = "analytics_dependency_admitted"

EXPECTED_SOURCE_SCHEMA_VERSION = "INT-OIA-060"
EXPECTED_SOURCE_AUTHORIZATION_SCHEMA_VERSION = (
    INT_OIA_060_AUTHORIZATION_SCHEMA_VERSION
)
EXPECTED_DEPENDENCY_STATUS = OOP_001_DEPENDENCY_STATUS
EXPECTED_OPERATOR_NAMESPACE = OPERATOR_PACKAGE_NAMESPACE


class OracleOperatorAnalyticsDependencyAdmissionInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
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
class OracleOperatorAnalyticsDependencyAdmission:
    admission_id: str
    source_dependency_receipt_id: str
    source_dependency_receipt_hash: str
    source_subsystem_boundary_hash: str
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
    admitted_consumer_id: str
    admitted_projection: str
    admitted_entry_count: int
    admitted_response_artifact_entry_ids: tuple[str, ...]
    admitted_query_response_ids: tuple[str, ...]
    dependency_receipt_type_verified: bool
    dependency_receipt_hash_verified: bool
    subsystem_boundary_verified: bool
    source_schema_verified: bool
    source_authorization_schema_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    entry_cardinality_verified: bool
    unique_entry_identities_verified: bool
    source_lineage_verified: bool
    deterministic_replay_verified: bool
    read_only_dependency_verified: bool
    operator_query_construction_allowed: bool
    operator_session_construction_allowed: bool
    operator_console_rendering_allowed: bool
    operator_presentation_rendering_allowed: bool
    analytics_reexecution_allowed: bool
    analytics_reexecution_performed: bool
    analytics_database_connection_allowed: bool
    analytics_database_connection_performed: bool
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
    admission_status: str
    admission_hash: str


class OracleOperatorAnalyticsDependencyAdmissionGate:
    @staticmethod
    def _verify_receipt(
        receipt: OracleOperatorAnalyticsDependencyReceipt,
    ) -> None:
        if not isinstance(receipt, OracleOperatorAnalyticsDependencyReceipt):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "source must be the canonical OOP-001 dependency receipt"
            )

        body = asdict(receipt)
        supplied_hash = body.pop("dependency_receipt_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "OOP-001 dependency receipt hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "OOP-001 dependency receipt hash mismatch"
            )

        if not _valid_sha256(receipt.dependency_receipt_id):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "OOP-001 dependency receipt identity is invalid"
            )
        if not _valid_sha256(receipt.subsystem_boundary_hash):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "OOP-001 subsystem boundary hash is invalid"
            )

        if receipt.source_schema_version != EXPECTED_SOURCE_SCHEMA_VERSION:
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "unexpected analytics source schema"
            )
        if (
            receipt.source_authorization_schema_version
            != EXPECTED_SOURCE_AUTHORIZATION_SCHEMA_VERSION
        ):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "unexpected INT-OIA-060 authorization schema"
            )
        if receipt.authorized_consumer_id != EXPECTED_CONSUMER_ID:
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "dependency receipt consumer identity mismatch"
            )
        if receipt.authorized_projection != EXPECTED_PROJECTION:
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "dependency receipt projection identity mismatch"
            )
        if receipt.dependency_status != EXPECTED_DEPENDENCY_STATUS:
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "dependency receipt is not in the read-only consumed state"
            )

        if receipt.authorized_entry_count < 1:
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "dependency receipt has no authorized entries"
            )
        if receipt.authorized_entry_count != len(
            receipt.authorized_response_artifact_entry_ids
        ):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if receipt.authorized_entry_count != len(
            receipt.authorized_query_response_ids
        ):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "query-response cardinality mismatch"
            )
        if len(
            set(receipt.authorized_response_artifact_entry_ids)
        ) != receipt.authorized_entry_count:
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(
            set(receipt.authorized_query_response_ids)
        ) != receipt.authorized_entry_count:
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "duplicate query-response identities detected"
            )

        required_hashes = (
            receipt.source_authorization_hash,
            receipt.source_attestation_hash,
            receipt.source_consumption_hash,
            receipt.source_registry_manifest_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "dependency lineage contains invalid hashes"
            )

        required_truths = (
            receipt.source_type_verified,
            receipt.source_hash_verified,
            receipt.source_lineage_verified,
            receipt.consumer_identity_verified,
            receipt.projection_identity_verified,
            receipt.deterministic_replay_verified,
            receipt.read_only_dependency_verified,
        )
        if not all(required_truths):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "dependency receipt is not fully verified"
            )

        forbidden_activity = (
            receipt.analytics_reexecution_performed,
            receipt.analytics_database_connection_performed,
            receipt.analytics_corpus_read_repeated,
            receipt.analytics_mutation_allowed,
            receipt.analytics_mutation_performed,
            receipt.publication_allowed,
            receipt.publication_performed,
            receipt.qseries_handoff_allowed,
            receipt.qseries_execution_allowed,
            receipt.qseries_execution_performed,
            receipt.order_creation_allowed,
            receipt.order_creation_performed,
            receipt.funds_movement_allowed,
            receipt.funds_movement_performed,
            receipt.portfolio_mutation_allowed,
            receipt.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorAnalyticsDependencyAdmissionInvariantError(
                "dependency receipt contains forbidden activity or authority"
            )

    def admit(
        self,
        *,
        receipt: OracleOperatorAnalyticsDependencyReceipt,
    ) -> OracleOperatorAnalyticsDependencyAdmission:
        self._verify_receipt(receipt)

        admission_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_dependency_receipt_id": receipt.dependency_receipt_id,
                "source_dependency_receipt_hash": (
                    receipt.dependency_receipt_hash
                ),
                "source_subsystem_boundary_hash": (
                    receipt.subsystem_boundary_hash
                ),
                "admitted_consumer_id": receipt.authorized_consumer_id,
                "admitted_projection": receipt.authorized_projection,
                "admitted_response_artifact_entry_ids": (
                    receipt.authorized_response_artifact_entry_ids
                ),
                "admitted_query_response_ids": (
                    receipt.authorized_query_response_ids
                ),
            }
        )

        body = {
            "admission_id": admission_id,
            "source_dependency_receipt_id": receipt.dependency_receipt_id,
            "source_dependency_receipt_hash": receipt.dependency_receipt_hash,
            "source_subsystem_boundary_hash": receipt.subsystem_boundary_hash,
            "source_schema_version": receipt.source_schema_version,
            "source_authorization_schema_version": (
                receipt.source_authorization_schema_version
            ),
            "source_authorization_id": receipt.source_authorization_id,
            "source_authorization_hash": receipt.source_authorization_hash,
            "source_attestation_id": receipt.source_attestation_id,
            "source_attestation_hash": receipt.source_attestation_hash,
            "source_consumption_id": receipt.source_consumption_id,
            "source_consumption_hash": receipt.source_consumption_hash,
            "source_registry_manifest_id": (
                receipt.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                receipt.source_registry_manifest_hash
            ),
            "admitted_consumer_id": receipt.authorized_consumer_id,
            "admitted_projection": receipt.authorized_projection,
            "admitted_entry_count": receipt.authorized_entry_count,
            "admitted_response_artifact_entry_ids": tuple(
                receipt.authorized_response_artifact_entry_ids
            ),
            "admitted_query_response_ids": tuple(
                receipt.authorized_query_response_ids
            ),
            "dependency_receipt_type_verified": True,
            "dependency_receipt_hash_verified": True,
            "subsystem_boundary_verified": True,
            "source_schema_verified": True,
            "source_authorization_schema_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "entry_cardinality_verified": True,
            "unique_entry_identities_verified": True,
            "source_lineage_verified": True,
            "deterministic_replay_verified": True,
            "read_only_dependency_verified": True,
            "operator_query_construction_allowed": True,
            "operator_session_construction_allowed": False,
            "operator_console_rendering_allowed": False,
            "operator_presentation_rendering_allowed": False,
            "analytics_reexecution_allowed": False,
            "analytics_reexecution_performed": False,
            "analytics_database_connection_allowed": False,
            "analytics_database_connection_performed": False,
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
            "admission_status": ADMISSION_STATUS,
        }

        return OracleOperatorAnalyticsDependencyAdmission(
            **body,
            admission_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ADMISSION_SCHEMA_VERSION",
    "ADMISSION_STATUS",
    "EXPECTED_SOURCE_SCHEMA_VERSION",
    "EXPECTED_SOURCE_AUTHORIZATION_SCHEMA_VERSION",
    "EXPECTED_DEPENDENCY_STATUS",
    "EXPECTED_OPERATOR_NAMESPACE",
    "OracleOperatorAnalyticsDependencyAdmission",
    "OracleOperatorAnalyticsDependencyAdmissionGate",
    "OracleOperatorAnalyticsDependencyAdmissionInvariantError",
    "stable_hash",
]
