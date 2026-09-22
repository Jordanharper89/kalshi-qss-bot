from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_activation_gate import (
    OracleCertifiedIntelligenceRegistryConsumptionActivation,
    verify_oracle_certified_intelligence_registry_consumption_activation,
)

ENGINE_ID = "INT-OII-005"
SCHEMA_VERSION = "INT-OII-005.v1"
ALGORITHM_VERSION = (
    "oracle-certified-intelligence-registry-consumption-activation-attestation.v1"
)
ATTESTATION_STATUS = (
    "oracle_certified_intelligence_registry_consumption_activation_attested"
)


class OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
    ValueError
):
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
class OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation:
    attestation_id: str
    source_activation_id: str
    source_activation_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_attestation_id: str
    source_attestation_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    activation_verified: bool
    exact_activation_hash_scope_preserved: bool
    exact_authorization_hash_scope_preserved: bool
    exact_attestation_hash_scope_preserved: bool
    exact_registry_hash_scope_preserved: bool
    exact_entry_hash_scope_preserved: bool
    certified_subsystem_scope_preserved: bool
    deterministic_activation_verified: bool
    bounded_registry_scope_verified: bool
    single_use_authorization_consumption_verified: bool
    duplicate_activation_rejection_verified: bool
    irreversible_activation_verified: bool
    read_only_consumption_activation_verified: bool
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
    attestation_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    attestation_hash: str


def attest_oracle_certified_intelligence_registry_consumption_activation(
    *,
    activation: OracleCertifiedIntelligenceRegistryConsumptionActivation,
) -> OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation:
    try:
        verdict = (
            verify_oracle_certified_intelligence_registry_consumption_activation(
                activation
            )
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "INT-OII-004 registry consumption activation verification failed"
        ) from exc

    if verdict is False:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "INT-OII-004 activation verifier returned false"
        )

    if activation.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "activated registry scope is empty"
        )

    if activation.source_entry_count != len(activation.source_entry_hashes):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "activated entry hash scope mismatch"
        )

    if activation.source_entry_count != len(activation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "activated subsystem scope mismatch"
        )

    body = {
        "source_activation_id": activation.activation_id,
        "source_activation_hash": activation.activation_hash,
        "source_authorization_id": activation.source_authorization_id,
        "source_authorization_hash": activation.source_authorization_hash,
        "source_attestation_id": activation.source_attestation_id,
        "source_attestation_hash": activation.source_attestation_hash,
        "source_registry_id": activation.source_registry_id,
        "source_registry_hash": activation.source_registry_hash,
        "source_entry_count": activation.source_entry_count,
        "source_entry_hashes": activation.source_entry_hashes,
        "source_subsystem_keys": activation.source_subsystem_keys,
        "activation_verified": True,
        "exact_activation_hash_scope_preserved": True,
        "exact_authorization_hash_scope_preserved": True,
        "exact_attestation_hash_scope_preserved": True,
        "exact_registry_hash_scope_preserved": True,
        "exact_entry_hash_scope_preserved": True,
        "certified_subsystem_scope_preserved": True,
        "deterministic_activation_verified": True,
        "bounded_registry_scope_verified": True,
        "single_use_authorization_consumption_verified": True,
        "duplicate_activation_rejection_verified": True,
        "irreversible_activation_verified": True,
        "read_only_consumption_activation_verified": True,
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
        "attestation_status": ATTESTATION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }

    attestation_hash = stable_hash(body)

    return OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation(
        attestation_id=(
            "oracle-certified-intelligence-registry-consumption-activation-attestation:"
            + attestation_hash
        ),
        **body,
        attestation_hash=attestation_hash,
    )


def verify_oracle_certified_intelligence_registry_consumption_activation_attestation(
    attestation: OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation,
) -> bool:
    if not isinstance(
        attestation,
        OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation,
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "invalid registry consumption activation attestation"
        )

    body = {
        key: value
        for key, value in asdict(attestation).items()
        if key not in {"attestation_id", "attestation_hash"}
    }
    expected_hash = stable_hash(body)

    if attestation.attestation_hash != expected_hash:
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "activation attestation hash mismatch"
        )

    if attestation.attestation_id != (
        "oracle-certified-intelligence-registry-consumption-activation-attestation:"
        + expected_hash
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "activation attestation identity mismatch"
        )

    if attestation.source_entry_count != len(attestation.source_entry_hashes):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "attested entry hash scope mismatch"
        )

    if attestation.source_entry_count != len(attestation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "attested subsystem scope mismatch"
        )

    if attestation.source_subsystem_keys != tuple(
        sorted(attestation.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "attested subsystem scope is not deterministic"
        )

    if len(attestation.source_subsystem_keys) != len(
        set(attestation.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "attested subsystem scope contains duplicates"
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

    required_true = (
        attestation.activation_verified,
        attestation.exact_activation_hash_scope_preserved,
        attestation.exact_authorization_hash_scope_preserved,
        attestation.exact_attestation_hash_scope_preserved,
        attestation.exact_registry_hash_scope_preserved,
        attestation.exact_entry_hash_scope_preserved,
        attestation.certified_subsystem_scope_preserved,
        attestation.deterministic_activation_verified,
        attestation.bounded_registry_scope_verified,
        attestation.single_use_authorization_consumption_verified,
        attestation.duplicate_activation_rejection_verified,
        attestation.irreversible_activation_verified,
        attestation.read_only_consumption_activation_verified,
        attestation.read_only,
    )

    if (
        attestation.engine_id != ENGINE_ID
        or attestation.schema_version != SCHEMA_VERSION
        or attestation.algorithm_version != ALGORITHM_VERSION
        or attestation.attestation_status != ATTESTATION_STATUS
        or attestation.source_entry_count <= 0
        or not all(value is True for value in required_true)
        or any(forbidden)
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError(
            "INT-OII-005 permanent safety boundary violated"
        )

    return True


def serialize_oracle_certified_intelligence_registry_consumption_activation_attestation(
    attestation: OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation,
) -> str:
    verify_oracle_certified_intelligence_registry_consumption_activation_attestation(
        attestation
    )
    return canonical_json(attestation)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ATTESTATION_STATUS",
    "OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError",
    "OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation",
    "attest_oracle_certified_intelligence_registry_consumption_activation",
    "verify_oracle_certified_intelligence_registry_consumption_activation_attestation",
    "serialize_oracle_certified_intelligence_registry_consumption_activation_attestation",
]
