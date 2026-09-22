from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,
    verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation,
)

ENGINE_ID = "INT-OII-013"
SCHEMA_VERSION = "INT-OII-013.v1"
ALGORITHM_VERSION = (
    "oracle-certified-intelligence-read-only-consumption-session-activation-authorization.v1"
)
AUTHORIZATION_STATUS = (
    "oracle_certified_intelligence_read_only_consumption_session_activation_authorized"
)


class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
    ValueError
):
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
class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization:
    authorization_id: str
    source_attestation_id: str
    source_attestation_hash: str
    source_activation_id: str
    source_activation_hash: str
    source_consumption_id: str
    source_consumption_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_readiness_id: str
    source_readiness_hash: str
    source_session_attestation_id: str
    source_session_attestation_hash: str
    source_session_id: str
    source_session_hash: str
    source_registry_activation_id: str
    source_registry_activation_hash: str
    source_registry_authorization_id: str
    source_registry_authorization_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    activation_attestation_verified: bool
    deterministic_authorization: bool
    bounded_authorization_scope: bool
    single_attestation_scope: bool
    authorization_single_use: bool
    duplicate_authorization_allowed: bool
    authorization_reversible: bool
    downstream_read_only_consumption_active: bool
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


def authorize_oracle_certified_intelligence_read_only_consumption_session_activation(
    *,
    attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,
) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization:
    try:
        verified = (
            verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(
                attestation
            )
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "INT-OII-012 activation attestation verification failed"
        ) from exc

    if verified is not True:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "INT-OII-012 activation attestation was not verified"
        )

    if attestation.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "certified subsystem scope is empty"
        )

    if attestation.source_entry_count != len(attestation.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "entry hash scope mismatch"
        )

    if attestation.source_entry_count != len(attestation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "subsystem scope mismatch"
        )

    if not attestation.downstream_read_only_consumption_active_attested:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "downstream read-only consumption is not attested active"
        )

    forbidden = (
        attestation.registry_mutation_allowed,
        attestation.oracle_execution_allowed,
        attestation.reasoning_execution_allowed,
        attestation.probability_estimation_allowed,
        attestation.final_intelligence_conclusion_allowed,
        attestation.publication_allowed,
        attestation.alerting_allowed,
        attestation.qseries_handoff_allowed,
        attestation.qseries_execution_allowed,
        attestation.order_creation_allowed,
        attestation.funds_movement_allowed,
        attestation.portfolio_mutation_allowed,
    )
    if any(forbidden) or not attestation.read_only:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "INT-OII-012 read-only boundary mismatch"
        )

    body = {
        "source_attestation_id": attestation.attestation_id,
        "source_attestation_hash": attestation.attestation_hash,
        "source_activation_id": attestation.source_activation_id,
        "source_activation_hash": attestation.source_activation_hash,
        "source_consumption_id": attestation.source_consumption_id,
        "source_consumption_hash": attestation.source_consumption_hash,
        "source_authorization_id": attestation.source_authorization_id,
        "source_authorization_hash": attestation.source_authorization_hash,
        "source_readiness_id": attestation.source_readiness_id,
        "source_readiness_hash": attestation.source_readiness_hash,
        "source_session_attestation_id": attestation.source_session_attestation_id,
        "source_session_attestation_hash": attestation.source_session_attestation_hash,
        "source_session_id": attestation.source_session_id,
        "source_session_hash": attestation.source_session_hash,
        "source_registry_activation_id": attestation.source_registry_activation_id,
        "source_registry_activation_hash": attestation.source_registry_activation_hash,
        "source_registry_authorization_id": attestation.source_registry_authorization_id,
        "source_registry_authorization_hash": attestation.source_registry_authorization_hash,
        "source_registry_id": attestation.source_registry_id,
        "source_registry_hash": attestation.source_registry_hash,
        "source_entry_count": attestation.source_entry_count,
        "source_entry_hashes": tuple(attestation.source_entry_hashes),
        "source_subsystem_keys": tuple(attestation.source_subsystem_keys),
        "activation_attestation_verified": True,
        "deterministic_authorization": True,
        "bounded_authorization_scope": True,
        "single_attestation_scope": True,
        "authorization_single_use": True,
        "duplicate_authorization_allowed": False,
        "authorization_reversible": False,
        "downstream_read_only_consumption_active": True,
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

    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization(
        authorization_id=(
            "oracle-certified-intelligence-read-only-consumption-session-activation-authorization:"
            + authorization_hash
        ),
        **body,
        authorization_hash=authorization_hash,
    )


def verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(
    authorization: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization,
) -> bool:
    if not isinstance(
        authorization,
        OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization,
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "invalid INT-OII-013 activation authorization"
        )

    body = asdict(authorization)
    authorization_id = body.pop("authorization_id")
    authorization_hash = body.pop("authorization_hash")

    expected_hash = _stable_hash(body)
    expected_id = (
        "oracle-certified-intelligence-read-only-consumption-session-activation-authorization:"
        + expected_hash
    )

    if authorization_hash != expected_hash or authorization_id != expected_id:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "authorization identity or hash mismatch"
        )

    required_true = (
        authorization.activation_attestation_verified,
        authorization.deterministic_authorization,
        authorization.bounded_authorization_scope,
        authorization.single_attestation_scope,
        authorization.authorization_single_use,
        authorization.downstream_read_only_consumption_active,
        authorization.read_only,
    )
    if not all(required_true):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "required authorization invariant is false"
        )

    forbidden = (
        authorization.duplicate_authorization_allowed,
        authorization.authorization_reversible,
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
    if any(forbidden):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "forbidden authorization capability enabled"
        )

    if authorization.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "empty authorization scope"
        )

    if authorization.source_entry_count != len(authorization.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "entry hash scope mismatch"
        )

    if authorization.source_entry_count != len(authorization.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "subsystem scope mismatch"
        )

    if authorization.authorization_status != AUTHORIZATION_STATUS:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "authorization status mismatch"
        )

    if authorization.engine_id != ENGINE_ID:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "engine id mismatch"
        )

    if authorization.schema_version != SCHEMA_VERSION:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "schema version mismatch"
        )

    if authorization.algorithm_version != ALGORITHM_VERSION:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(
            "algorithm version mismatch"
        )

    return True
