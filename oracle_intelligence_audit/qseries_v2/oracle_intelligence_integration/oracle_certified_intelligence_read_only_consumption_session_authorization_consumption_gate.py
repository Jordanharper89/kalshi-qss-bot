from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_authorization_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization,
    verify_oracle_certified_intelligence_read_only_consumption_session_authorization,
)

ENGINE_ID = "INT-OII-010"
SCHEMA_VERSION = "INT-OII-010.v1"
ALGORITHM_VERSION = "oracle-certified-intelligence-read-only-consumption-session-authorization-consumption.v1"
CONSUMPTION_STATUS = "oracle_certified_intelligence_read_only_consumption_session_authorization_consumed"


class OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(ValueError):
    pass


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _stable_hash(value: object) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption:
    consumption_id: str
    source_authorization_id: str
    source_authorization_hash: str
    source_readiness_id: str
    source_readiness_hash: str
    source_session_attestation_id: str
    source_session_attestation_hash: str
    source_session_id: str
    source_session_hash: str
    source_activation_id: str
    source_activation_hash: str
    source_registry_authorization_id: str
    source_registry_authorization_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    authorization_verified: bool
    deterministic_consumption: bool
    bounded_consumption_scope: bool
    single_authorization_scope: bool
    single_use_authorization_consumed: bool
    duplicate_consumption_allowed: bool
    consumption_reversible: bool
    downstream_read_only_consumption_activated: bool
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
    consumption_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    consumption_hash: str


def consume_oracle_certified_intelligence_read_only_consumption_session_authorization(
    *,
    authorization: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization,
) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption:
    try:
        verified = verify_oracle_certified_intelligence_read_only_consumption_session_authorization(
            authorization
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "INT-OII-009 authorization verification failed"
        ) from exc

    if verified is not True:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "INT-OII-009 authorization was not verified"
        )
    if authorization.authorization_consumed:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "authorization is already consumed"
        )
    if not authorization.authorization_single_use:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "authorization is not single-use"
        )
    if authorization.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "certified subsystem scope is empty"
        )
    if authorization.source_entry_count != len(authorization.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "entry hash scope mismatch"
        )
    if authorization.source_entry_count != len(authorization.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "subsystem scope mismatch"
        )

    body = {
        "source_authorization_id": authorization.authorization_id,
        "source_authorization_hash": authorization.authorization_hash,
        "source_readiness_id": authorization.source_readiness_id,
        "source_readiness_hash": authorization.source_readiness_hash,
        "source_session_attestation_id": authorization.source_session_attestation_id,
        "source_session_attestation_hash": authorization.source_session_attestation_hash,
        "source_session_id": authorization.source_session_id,
        "source_session_hash": authorization.source_session_hash,
        "source_activation_id": authorization.source_activation_id,
        "source_activation_hash": authorization.source_activation_hash,
        "source_registry_authorization_id": authorization.source_authorization_id,
        "source_registry_authorization_hash": authorization.source_authorization_hash,
        "source_registry_id": authorization.source_registry_id,
        "source_registry_hash": authorization.source_registry_hash,
        "source_entry_count": authorization.source_entry_count,
        "source_entry_hashes": tuple(authorization.source_entry_hashes),
        "source_subsystem_keys": tuple(authorization.source_subsystem_keys),
        "authorization_verified": True,
        "deterministic_consumption": True,
        "bounded_consumption_scope": True,
        "single_authorization_scope": True,
        "single_use_authorization_consumed": True,
        "duplicate_consumption_allowed": False,
        "consumption_reversible": False,
        "downstream_read_only_consumption_activated": True,
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
        "consumption_status": CONSUMPTION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    consumption_hash = _stable_hash(body)
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption(
        consumption_id="oracle-certified-intelligence-read-only-consumption-session-authorization-consumption:" + consumption_hash,
        **body,
        consumption_hash=consumption_hash,
    )


def verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption(
    consumption: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption,
) -> bool:
    if not isinstance(
        consumption,
        OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption,
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "invalid INT-OII-010 authorization consumption"
        )

    body = asdict(consumption)
    consumption_id = body.pop("consumption_id")
    consumption_hash = body.pop("consumption_hash")
    expected_hash = _stable_hash(body)
    expected_id = "oracle-certified-intelligence-read-only-consumption-session-authorization-consumption:" + expected_hash

    if consumption_hash != expected_hash or consumption_id != expected_id:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "consumption identity or hash mismatch"
        )
    if consumption.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "empty consumption scope"
        )
    if consumption.source_entry_count != len(consumption.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "entry hash scope mismatch"
        )
    if consumption.source_entry_count != len(consumption.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "subsystem scope mismatch"
        )

    required_true = (
        consumption.authorization_verified,
        consumption.deterministic_consumption,
        consumption.bounded_consumption_scope,
        consumption.single_authorization_scope,
        consumption.single_use_authorization_consumed,
        consumption.downstream_read_only_consumption_activated,
        consumption.read_only,
    )
    forbidden = (
        consumption.duplicate_consumption_allowed,
        consumption.consumption_reversible,
        consumption.registry_mutation_allowed,
        consumption.oracle_execution_allowed,
        consumption.reasoning_execution_allowed,
        consumption.probability_estimation_allowed,
        consumption.final_intelligence_conclusion_allowed,
        consumption.publication_allowed,
        consumption.alerting_allowed,
        consumption.qseries_handoff_allowed,
        consumption.qseries_execution_allowed,
        consumption.order_creation_allowed,
        consumption.funds_movement_allowed,
        consumption.portfolio_mutation_allowed,
    )

    if (
        not all(required_true)
        or any(forbidden)
        or consumption.engine_id != ENGINE_ID
        or consumption.schema_version != SCHEMA_VERSION
        or consumption.algorithm_version != ALGORITHM_VERSION
        or consumption.consumption_status != CONSUMPTION_STATUS
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError(
            "INT-OII-010 permanent safety boundary violated"
        )
    return True


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "CONSUMPTION_STATUS",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption",
    "consume_oracle_certified_intelligence_read_only_consumption_session_authorization",
    "verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption",
]
