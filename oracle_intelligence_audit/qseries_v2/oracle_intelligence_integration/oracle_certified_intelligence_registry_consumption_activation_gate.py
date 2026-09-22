from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_authorization_gate import (
    OracleCertifiedIntelligenceRegistryConsumptionAuthorization,
    verify_oracle_certified_intelligence_registry_consumption_authorization,
)

ENGINE_ID = "INT-OII-004"
SCHEMA_VERSION = "INT-OII-004.v1"
ALGORITHM_VERSION = "oracle-certified-intelligence-registry-consumption-activation.v1"
ACTIVATION_STATUS = "oracle_certified_intelligence_registry_consumption_activated"


class OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OracleCertifiedIntelligenceRegistryConsumptionActivation:
    activation_id: str
    source_authorization_id: str
    source_authorization_hash: str
    source_attestation_id: str
    source_attestation_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    authorization_verified: bool
    exact_authorization_hash_scope_preserved: bool
    exact_attestation_hash_scope_preserved: bool
    exact_registry_hash_scope_preserved: bool
    exact_entry_hash_scope_preserved: bool
    certified_subsystem_scope_preserved: bool
    read_only_consumption_activated: bool
    deterministic_activation: bool
    bounded_registry_scope_preserved: bool
    single_use_authorization_consumed: bool
    duplicate_activation_rejected: bool
    activation_reversible: bool
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


def activate_oracle_certified_intelligence_registry_consumption(
    *,
    authorization: OracleCertifiedIntelligenceRegistryConsumptionAuthorization,
) -> OracleCertifiedIntelligenceRegistryConsumptionActivation:
    try:
        verdict = (
            verify_oracle_certified_intelligence_registry_consumption_authorization(
                authorization
            )
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "INT-OII-003 registry consumption authorization verification failed"
        ) from exc

    if verdict is False:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "INT-OII-003 authorization verifier returned false"
        )

    if authorization.authorization_consumed is not False:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "authorization has already been consumed"
        )

    if authorization.single_use_authorization_required is not True:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "single-use authorization requirement missing"
        )

    if authorization.read_only_consumption_authorized is not True:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "read-only registry consumption is not authorized"
        )

    if authorization.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "authorized registry scope is empty"
        )

    if authorization.source_entry_count != len(
        authorization.source_entry_hashes
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "authorized entry hash scope mismatch"
        )

    if authorization.source_entry_count != len(
        authorization.source_subsystem_keys
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "authorized subsystem scope mismatch"
        )

    body = {
        "source_authorization_id": authorization.authorization_id,
        "source_authorization_hash": authorization.authorization_hash,
        "source_attestation_id": authorization.source_attestation_id,
        "source_attestation_hash": authorization.source_attestation_hash,
        "source_registry_id": authorization.source_registry_id,
        "source_registry_hash": authorization.source_registry_hash,
        "source_entry_count": authorization.source_entry_count,
        "source_entry_hashes": authorization.source_entry_hashes,
        "source_subsystem_keys": authorization.source_subsystem_keys,
        "authorization_verified": True,
        "exact_authorization_hash_scope_preserved": True,
        "exact_attestation_hash_scope_preserved": True,
        "exact_registry_hash_scope_preserved": True,
        "exact_entry_hash_scope_preserved": True,
        "certified_subsystem_scope_preserved": True,
        "read_only_consumption_activated": True,
        "deterministic_activation": True,
        "bounded_registry_scope_preserved": True,
        "single_use_authorization_consumed": True,
        "duplicate_activation_rejected": True,
        "activation_reversible": False,
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

    activation_hash = stable_hash(body)

    return OracleCertifiedIntelligenceRegistryConsumptionActivation(
        activation_id=(
            "oracle-certified-intelligence-registry-consumption-activation:"
            + activation_hash
        ),
        **body,
        activation_hash=activation_hash,
    )


def verify_oracle_certified_intelligence_registry_consumption_activation(
    activation: OracleCertifiedIntelligenceRegistryConsumptionActivation,
) -> bool:
    if not isinstance(
        activation,
        OracleCertifiedIntelligenceRegistryConsumptionActivation,
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "invalid registry consumption activation"
        )

    body = {
        key: value
        for key, value in asdict(activation).items()
        if key not in {"activation_id", "activation_hash"}
    }
    expected_hash = stable_hash(body)

    if activation.activation_hash != expected_hash:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "registry consumption activation hash mismatch"
        )

    if activation.activation_id != (
        "oracle-certified-intelligence-registry-consumption-activation:"
        + expected_hash
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "registry consumption activation identity mismatch"
        )

    if activation.source_entry_count != len(activation.source_entry_hashes):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "activated entry hash scope mismatch"
        )

    if activation.source_entry_count != len(activation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "activated subsystem scope mismatch"
        )

    if activation.source_subsystem_keys != tuple(
        sorted(activation.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "activated subsystem scope is not deterministic"
        )

    if len(activation.source_subsystem_keys) != len(
        set(activation.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "activated subsystem scope contains duplicates"
        )

    forbidden = (
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
        activation.engine_id != ENGINE_ID
        or activation.schema_version != SCHEMA_VERSION
        or activation.algorithm_version != ALGORITHM_VERSION
        or activation.activation_status != ACTIVATION_STATUS
        or activation.source_entry_count <= 0
        or activation.authorization_verified is not True
        or activation.exact_authorization_hash_scope_preserved is not True
        or activation.exact_attestation_hash_scope_preserved is not True
        or activation.exact_registry_hash_scope_preserved is not True
        or activation.exact_entry_hash_scope_preserved is not True
        or activation.certified_subsystem_scope_preserved is not True
        or activation.read_only_consumption_activated is not True
        or activation.deterministic_activation is not True
        or activation.bounded_registry_scope_preserved is not True
        or activation.single_use_authorization_consumed is not True
        or activation.duplicate_activation_rejected is not True
        or activation.read_only is not True
        or any(forbidden)
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(
            "INT-OII-004 permanent safety boundary violated"
        )

    return True


def serialize_oracle_certified_intelligence_registry_consumption_activation(
    activation: OracleCertifiedIntelligenceRegistryConsumptionActivation,
) -> str:
    verify_oracle_certified_intelligence_registry_consumption_activation(
        activation
    )
    return canonical_json(activation)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ACTIVATION_STATUS",
    "OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError",
    "OracleCertifiedIntelligenceRegistryConsumptionActivation",
    "activate_oracle_certified_intelligence_registry_consumption",
    "verify_oracle_certified_intelligence_registry_consumption_activation",
    "serialize_oracle_certified_intelligence_registry_consumption_activation",
]
