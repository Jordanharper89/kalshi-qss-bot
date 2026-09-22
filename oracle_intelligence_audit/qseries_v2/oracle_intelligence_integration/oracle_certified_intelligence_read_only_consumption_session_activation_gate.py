from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_authorization_consumption_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption,
    verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption,
)

ENGINE_ID = "INT-OII-011"
SCHEMA_VERSION = "INT-OII-011.v1"
ALGORITHM_VERSION = (
    "oracle-certified-intelligence-read-only-consumption-session-activation.v1"
)
ACTIVATION_STATUS = (
    "oracle_certified_intelligence_read_only_consumption_session_activated"
)


class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
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
class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation:
    activation_id: str
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
    authorization_consumption_verified: bool
    deterministic_activation: bool
    bounded_activation_scope: bool
    single_consumption_scope: bool
    activation_single_use: bool
    duplicate_activation_allowed: bool
    activation_reversible: bool
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
    activation_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    activation_hash: str


def activate_oracle_certified_intelligence_read_only_consumption_session(
    *,
    consumption: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption,
) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation:
    try:
        verified = (
            verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption(
                consumption
            )
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "INT-OII-010 authorization consumption verification failed"
        ) from exc

    if verified is not True:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "INT-OII-010 authorization consumption was not verified"
        )

    if not consumption.single_use_authorization_consumed:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "single-use authorization consumption is not complete"
        )

    if not consumption.downstream_read_only_consumption_activated:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "downstream read-only consumption is not activated"
        )

    if consumption.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "certified subsystem scope is empty"
        )

    if consumption.source_entry_count != len(consumption.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "entry hash scope mismatch"
        )

    if consumption.source_entry_count != len(consumption.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "subsystem scope mismatch"
        )

    body = {
        "source_consumption_id": consumption.consumption_id,
        "source_consumption_hash": consumption.consumption_hash,
        "source_authorization_id": consumption.source_authorization_id,
        "source_authorization_hash": consumption.source_authorization_hash,
        "source_readiness_id": consumption.source_readiness_id,
        "source_readiness_hash": consumption.source_readiness_hash,
        "source_session_attestation_id": consumption.source_session_attestation_id,
        "source_session_attestation_hash": consumption.source_session_attestation_hash,
        "source_session_id": consumption.source_session_id,
        "source_session_hash": consumption.source_session_hash,
        "source_registry_activation_id": consumption.source_activation_id,
        "source_registry_activation_hash": consumption.source_activation_hash,
        "source_registry_authorization_id": consumption.source_registry_authorization_id,
        "source_registry_authorization_hash": consumption.source_registry_authorization_hash,
        "source_registry_id": consumption.source_registry_id,
        "source_registry_hash": consumption.source_registry_hash,
        "source_entry_count": consumption.source_entry_count,
        "source_entry_hashes": tuple(consumption.source_entry_hashes),
        "source_subsystem_keys": tuple(consumption.source_subsystem_keys),
        "authorization_consumption_verified": True,
        "deterministic_activation": True,
        "bounded_activation_scope": True,
        "single_consumption_scope": True,
        "activation_single_use": True,
        "duplicate_activation_allowed": False,
        "activation_reversible": False,
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
        "activation_status": ACTIVATION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }

    activation_hash = _stable_hash(body)

    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation(
        activation_id=(
            "oracle-certified-intelligence-read-only-consumption-session-activation:"
            + activation_hash
        ),
        **body,
        activation_hash=activation_hash,
    )


def verify_oracle_certified_intelligence_read_only_consumption_session_activation(
    activation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,
) -> bool:
    if not isinstance(
        activation,
        OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "invalid INT-OII-011 activation"
        )

    body = asdict(activation)
    activation_id = body.pop("activation_id")
    activation_hash = body.pop("activation_hash")

    expected_hash = _stable_hash(body)
    expected_id = (
        "oracle-certified-intelligence-read-only-consumption-session-activation:"
        + expected_hash
    )

    if activation_hash != expected_hash or activation_id != expected_id:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "activation identity or hash mismatch"
        )

    if activation.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "empty activation scope"
        )

    if activation.source_entry_count != len(activation.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "entry hash scope mismatch"
        )

    if activation.source_entry_count != len(activation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "subsystem scope mismatch"
        )

    required_true = (
        activation.authorization_consumption_verified,
        activation.deterministic_activation,
        activation.bounded_activation_scope,
        activation.single_consumption_scope,
        activation.activation_single_use,
        activation.downstream_read_only_consumption_active,
        activation.read_only,
    )

    forbidden = (
        activation.duplicate_activation_allowed,
        activation.activation_reversible,
        activation.registry_mutation_allowed,
        activation.oracle_execution_allowed,
        activation.reasoning_execution_allowed,
        activation.probability_estimation_allowed,
        activation.final_intelligence_conclusion_allowed,
        activation.publication_allowed,
        activation.alerting_allowed,
        activation.qseries_handoff_allowed,
        activation.qseries_execution_allowed,
        activation.order_creation_allowed,
        activation.funds_movement_allowed,
        activation.portfolio_mutation_allowed,
    )

    if (
        not all(required_true)
        or any(forbidden)
        or activation.engine_id != ENGINE_ID
        or activation.schema_version != SCHEMA_VERSION
        or activation.algorithm_version != ALGORITHM_VERSION
        or activation.activation_status != ACTIVATION_STATUS
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(
            "INT-OII-011 permanent safety boundary violated"
        )

    return True


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ACTIVATION_STATUS",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation",
    "activate_oracle_certified_intelligence_read_only_consumption_session",
    "verify_oracle_certified_intelligence_read_only_consumption_session_activation",
]
