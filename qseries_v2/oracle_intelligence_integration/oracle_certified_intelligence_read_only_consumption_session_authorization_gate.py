from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_readiness_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness,
    verify_oracle_certified_intelligence_read_only_consumption_session_readiness,
)

ENGINE_ID = "INT-OII-009"
SCHEMA_VERSION = "INT-OII-009.v2"
ALGORITHM_VERSION = "oracle-certified-intelligence-read-only-consumption-session-authorization.v2"
AUTHORIZATION_STATUS = "oracle_certified_intelligence_read_only_consumption_session_authorized"


class OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(ValueError):
    pass


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _stable_hash(value: object) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization:
    authorization_id: str
    source_readiness_id: str
    source_readiness_hash: str
    source_session_attestation_id: str
    source_session_attestation_hash: str
    source_session_id: str
    source_session_hash: str
    source_activation_id: str
    source_activation_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    readiness_verified: bool
    deterministic_authorization: bool
    bounded_authorization_scope: bool
    single_session_scope: bool
    authorization_single_use: bool
    authorization_consumed: bool
    downstream_read_only_consumption_authorized: bool
    registry_mutation_allowed: bool
    oracle_execution_allowed: bool
    reasoning_execution_allowed: bool
    probability_estimation_allowed: bool
    final_intelligence_conclusion_allowed: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    read_only: bool
    authorization_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    authorization_hash: str


def authorize_oracle_certified_intelligence_read_only_consumption_session(
    *,
    readiness: OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness,
) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization:
    try:
        verified = verify_oracle_certified_intelligence_read_only_consumption_session_readiness(readiness)
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "INT-OII-008 readiness verification failed"
        ) from exc

    if verified is not True:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "INT-OII-008 readiness was not verified"
        )

    if readiness.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "certified subsystem scope is empty"
        )
    if readiness.source_entry_count != len(readiness.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "entry hash scope mismatch"
        )
    if readiness.source_entry_count != len(readiness.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "subsystem scope mismatch"
        )

    body = {
        "source_readiness_id": readiness.readiness_id,
        "source_readiness_hash": readiness.readiness_hash,
        "source_session_attestation_id": readiness.source_session_attestation_id,
        "source_session_attestation_hash": readiness.source_session_attestation_hash,
        "source_session_id": readiness.source_session_id,
        "source_session_hash": readiness.source_session_hash,
        "source_activation_id": readiness.source_activation_id,
        "source_activation_hash": readiness.source_activation_hash,
        "source_authorization_id": readiness.source_authorization_id,
        "source_authorization_hash": readiness.source_authorization_hash,
        "source_registry_id": readiness.source_registry_id,
        "source_registry_hash": readiness.source_registry_hash,
        "source_entry_count": readiness.source_entry_count,
        "source_entry_hashes": tuple(readiness.source_entry_hashes),
        "source_subsystem_keys": tuple(readiness.source_subsystem_keys),
        "readiness_verified": True,
        "deterministic_authorization": True,
        "bounded_authorization_scope": True,
        "single_session_scope": True,
        "authorization_single_use": True,
        "authorization_consumed": False,
        "downstream_read_only_consumption_authorized": True,
        "registry_mutation_allowed": False,
        "oracle_execution_allowed": False,
        "reasoning_execution_allowed": False,
        "probability_estimation_allowed": False,
        "final_intelligence_conclusion_allowed": False,
        "publication_allowed": False,
        "alerting_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "read_only": True,
        "authorization_status": AUTHORIZATION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    authorization_hash = _stable_hash(body)
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization(
        authorization_id="oracle-certified-intelligence-read-only-consumption-session-authorization:" + authorization_hash,
        **body,
        authorization_hash=authorization_hash,
    )


def verify_oracle_certified_intelligence_read_only_consumption_session_authorization(
    authorization: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization,
) -> bool:
    if not isinstance(authorization, OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "invalid INT-OII-009 authorization"
        )

    body = asdict(authorization)
    authorization_id = body.pop("authorization_id")
    authorization_hash = body.pop("authorization_hash")
    expected_hash = _stable_hash(body)
    expected_id = "oracle-certified-intelligence-read-only-consumption-session-authorization:" + expected_hash

    if authorization_hash != expected_hash or authorization_id != expected_id:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "authorization identity or hash mismatch"
        )
    if authorization.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "empty authorization scope"
        )
    if authorization.source_entry_count != len(authorization.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "entry hash scope mismatch"
        )
    if authorization.source_entry_count != len(authorization.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "subsystem scope mismatch"
        )

    required_true = (
        authorization.readiness_verified,
        authorization.deterministic_authorization,
        authorization.bounded_authorization_scope,
        authorization.single_session_scope,
        authorization.authorization_single_use,
        authorization.downstream_read_only_consumption_authorized,
        authorization.read_only,
    )
    forbidden = (
        authorization.authorization_consumed,
        authorization.registry_mutation_allowed,
        authorization.oracle_execution_allowed,
        authorization.reasoning_execution_allowed,
        authorization.probability_estimation_allowed,
        authorization.final_intelligence_conclusion_allowed,
        authorization.publication_allowed,
        authorization.alerting_allowed,
        authorization.qseries_handoff_allowed,
        authorization.qseries_execution_allowed,
        authorization.order_creation_allowed,
        authorization.funds_movement_allowed,
        authorization.portfolio_mutation_allowed,
    )

    if (
        not all(required_true)
        or any(forbidden)
        or authorization.engine_id != ENGINE_ID
        or authorization.schema_version != SCHEMA_VERSION
        or authorization.algorithm_version != ALGORITHM_VERSION
        or authorization.authorization_status != AUTHORIZATION_STATUS
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError(
            "INT-OII-009 permanent safety boundary violated"
        )
    return True


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "AUTHORIZATION_STATUS",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization",
    "authorize_oracle_certified_intelligence_read_only_consumption_session",
    "verify_oracle_certified_intelligence_read_only_consumption_session_authorization",
]
