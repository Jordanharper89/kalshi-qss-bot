from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,
    verify_oracle_certified_intelligence_read_only_consumption_session_activation,
)

ENGINE_ID = "INT-OII-012"
SCHEMA_VERSION = "INT-OII-012.v1"
ALGORITHM_VERSION = (
    "oracle-certified-intelligence-read-only-consumption-session-activation-attestation.v1"
)
ATTESTATION_STATUS = (
    "oracle_certified_intelligence_read_only_consumption_session_activation_attested"
)


class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
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
class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation:
    attestation_id: str
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
    activation_verified: bool
    activation_identity_attested: bool
    activation_hash_attested: bool
    complete_lineage_attested: bool
    deterministic_attestation: bool
    bounded_attestation_scope: bool
    single_activation_scope: bool
    activation_single_use_attested: bool
    duplicate_activation_disabled_attested: bool
    irreversible_activation_attested: bool
    downstream_read_only_consumption_active_attested: bool
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


def attest_oracle_certified_intelligence_read_only_consumption_session_activation(
    *,
    activation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,
) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation:
    try:
        verified = (
            verify_oracle_certified_intelligence_read_only_consumption_session_activation(
                activation
            )
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "INT-OII-011 activation verification failed"
        ) from exc

    if verified is not True:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "INT-OII-011 activation was not verified"
        )

    if not activation.activation_single_use:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "activation is not single-use"
        )

    if activation.duplicate_activation_allowed:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "duplicate activation is allowed"
        )

    if activation.activation_reversible:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "activation is reversible"
        )

    if not activation.downstream_read_only_consumption_active:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "downstream read-only consumption is not active"
        )

    if activation.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "certified subsystem scope is empty"
        )

    if activation.source_entry_count != len(activation.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "entry hash scope mismatch"
        )

    if activation.source_entry_count != len(activation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "subsystem scope mismatch"
        )

    body = {
        "source_activation_id": activation.activation_id,
        "source_activation_hash": activation.activation_hash,
        "source_consumption_id": activation.source_consumption_id,
        "source_consumption_hash": activation.source_consumption_hash,
        "source_authorization_id": activation.source_authorization_id,
        "source_authorization_hash": activation.source_authorization_hash,
        "source_readiness_id": activation.source_readiness_id,
        "source_readiness_hash": activation.source_readiness_hash,
        "source_session_attestation_id": activation.source_session_attestation_id,
        "source_session_attestation_hash": activation.source_session_attestation_hash,
        "source_session_id": activation.source_session_id,
        "source_session_hash": activation.source_session_hash,
        "source_registry_activation_id": activation.source_registry_activation_id,
        "source_registry_activation_hash": activation.source_registry_activation_hash,
        "source_registry_authorization_id": activation.source_registry_authorization_id,
        "source_registry_authorization_hash": activation.source_registry_authorization_hash,
        "source_registry_id": activation.source_registry_id,
        "source_registry_hash": activation.source_registry_hash,
        "source_entry_count": activation.source_entry_count,
        "source_entry_hashes": tuple(activation.source_entry_hashes),
        "source_subsystem_keys": tuple(activation.source_subsystem_keys),
        "activation_verified": True,
        "activation_identity_attested": True,
        "activation_hash_attested": True,
        "complete_lineage_attested": True,
        "deterministic_attestation": True,
        "bounded_attestation_scope": True,
        "single_activation_scope": True,
        "activation_single_use_attested": True,
        "duplicate_activation_disabled_attested": True,
        "irreversible_activation_attested": True,
        "downstream_read_only_consumption_active_attested": True,
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

    attestation_hash = _stable_hash(body)

    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation(
        attestation_id=(
            "oracle-certified-intelligence-read-only-consumption-session-activation-attestation:"
            + attestation_hash
        ),
        **body,
        attestation_hash=attestation_hash,
    )


def verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(
    attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,
) -> bool:
    if not isinstance(
        attestation,
        OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "invalid INT-OII-012 activation attestation"
        )

    body = asdict(attestation)
    attestation_id = body.pop("attestation_id")
    attestation_hash = body.pop("attestation_hash")

    expected_hash = _stable_hash(body)
    expected_id = (
        "oracle-certified-intelligence-read-only-consumption-session-activation-attestation:"
        + expected_hash
    )

    if attestation_hash != expected_hash or attestation_id != expected_id:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "attestation identity or hash mismatch"
        )

    if attestation.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "empty attestation scope"
        )

    if attestation.source_entry_count != len(attestation.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "entry hash scope mismatch"
        )

    if attestation.source_entry_count != len(attestation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "subsystem scope mismatch"
        )

    required_true = (
        attestation.activation_verified,
        attestation.activation_identity_attested,
        attestation.activation_hash_attested,
        attestation.complete_lineage_attested,
        attestation.deterministic_attestation,
        attestation.bounded_attestation_scope,
        attestation.single_activation_scope,
        attestation.activation_single_use_attested,
        attestation.duplicate_activation_disabled_attested,
        attestation.irreversible_activation_attested,
        attestation.downstream_read_only_consumption_active_attested,
        attestation.read_only,
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

    if (
        not all(required_true)
        or any(forbidden)
        or attestation.engine_id != ENGINE_ID
        or attestation.schema_version != SCHEMA_VERSION
        or attestation.algorithm_version != ALGORITHM_VERSION
        or attestation.attestation_status != ATTESTATION_STATUS
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(
            "INT-OII-012 permanent safety boundary violated"
        )

    return True


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ATTESTATION_STATUS",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation",
    "attest_oracle_certified_intelligence_read_only_consumption_session_activation",
    "verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation",
]
