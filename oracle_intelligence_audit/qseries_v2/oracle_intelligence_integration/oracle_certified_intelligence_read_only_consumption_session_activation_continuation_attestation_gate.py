from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation,
    verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation,
)

ENGINE_ID = "INT-OII-016"
SCHEMA_VERSION = "INT-OII-016.v1"
ALGORITHM_VERSION = "oracle-certified-intelligence-read-only-consumption-session-activation-continuation-attestation.v1"
ATTESTATION_STATUS = "oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attested"


class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(ValueError):
    pass


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _stable_hash(value: object) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation:
    attestation_id: str
    source_continuation_id: str
    source_continuation_hash: str
    source_authorization_consumption_id: str
    source_authorization_consumption_hash: str
    source_activation_authorization_id: str
    source_activation_authorization_hash: str
    source_activation_id: str
    source_activation_hash: str
    source_session_id: str
    source_session_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    continuation_verified: bool
    deterministic_attestation: bool
    bounded_attestation_scope: bool
    single_continuation_scope: bool
    attestation_single_use: bool
    duplicate_attestation_allowed: bool
    attestation_reversible: bool
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
    attestation_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    attestation_hash: str


def attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(
    *, continuation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation
) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation:
    try:
        verified = verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(continuation)
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(
            "INT-OII-015 continuation verification failed"
        ) from exc
    if verified is not True:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(
            "INT-OII-015 continuation was not verified"
        )
    if (
        continuation.source_entry_count <= 0
        or continuation.source_entry_count != len(continuation.source_entry_hashes)
        or continuation.source_entry_count != len(continuation.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(
            "certified subsystem scope mismatch"
        )
    required = (
        continuation.authorization_consumption_verified,
        continuation.deterministic_continuation,
        continuation.bounded_continuation_scope,
        continuation.single_consumption_scope,
        continuation.continuation_single_use,
        continuation.downstream_read_only_consumption_active,
        continuation.read_only,
    )
    forbidden = (
        continuation.duplicate_continuation_allowed,
        continuation.continuation_reversible,
        continuation.registry_mutation_allowed,
        continuation.oracle_execution_allowed,
        continuation.reasoning_execution_allowed,
        continuation.probability_estimation_allowed,
        continuation.final_intelligence_conclusion_allowed,
        continuation.publication_allowed,
        continuation.alerting_allowed,
        continuation.qseries_handoff_allowed,
        continuation.qseries_execution_allowed,
        continuation.order_creation_allowed,
        continuation.funds_movement_allowed,
        continuation.portfolio_mutation_allowed,
    )
    if not all(required) or any(forbidden):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(
            "INT-OII-015 read-only boundary mismatch"
        )
    body = {
        "source_continuation_id": continuation.continuation_id,
        "source_continuation_hash": continuation.continuation_hash,
        "source_authorization_consumption_id": continuation.source_authorization_consumption_id,
        "source_authorization_consumption_hash": continuation.source_authorization_consumption_hash,
        "source_activation_authorization_id": continuation.source_activation_authorization_id,
        "source_activation_authorization_hash": continuation.source_activation_authorization_hash,
        "source_activation_id": continuation.source_activation_id,
        "source_activation_hash": continuation.source_activation_hash,
        "source_session_id": continuation.source_session_id,
        "source_session_hash": continuation.source_session_hash,
        "source_registry_id": continuation.source_registry_id,
        "source_registry_hash": continuation.source_registry_hash,
        "source_entry_count": continuation.source_entry_count,
        "source_entry_hashes": tuple(continuation.source_entry_hashes),
        "source_subsystem_keys": tuple(continuation.source_subsystem_keys),
        "continuation_verified": True,
        "deterministic_attestation": True,
        "bounded_attestation_scope": True,
        "single_continuation_scope": True,
        "attestation_single_use": True,
        "duplicate_attestation_allowed": False,
        "attestation_reversible": False,
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
        "attestation_status": ATTESTATION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    attestation_hash = _stable_hash(body)
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation(
        attestation_id="oracle-certified-intelligence-read-only-consumption-session-activation-continuation-attestation:" + attestation_hash,
        **body,
        attestation_hash=attestation_hash,
    )


def verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation(
    value: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation,
) -> bool:
    if not isinstance(value, OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(
            "invalid INT-OII-016 attestation type"
        )
    body = asdict(value)
    supplied_hash = body.pop("attestation_hash")
    body.pop("attestation_id")
    expected_hash = _stable_hash(body)
    if supplied_hash != expected_hash:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(
            "INT-OII-016 attestation hash mismatch"
        )
    expected_id = "oracle-certified-intelligence-read-only-consumption-session-activation-continuation-attestation:" + expected_hash
    if value.attestation_id != expected_id:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(
            "INT-OII-016 attestation id mismatch"
        )
    required = (
        value.continuation_verified,
        value.deterministic_attestation,
        value.bounded_attestation_scope,
        value.single_continuation_scope,
        value.attestation_single_use,
        value.downstream_read_only_consumption_active,
        value.read_only,
    )
    forbidden = (
        value.duplicate_attestation_allowed,
        value.attestation_reversible,
        value.registry_mutation_allowed,
        value.oracle_execution_allowed,
        value.reasoning_execution_allowed,
        value.probability_estimation_allowed,
        value.final_intelligence_conclusion_allowed,
        value.publication_allowed,
        value.alerting_allowed,
        value.qseries_handoff_allowed,
        value.qseries_execution_allowed,
        value.order_creation_allowed,
        value.funds_movement_allowed,
        value.portfolio_mutation_allowed,
    )
    if (
        not all(required)
        or any(forbidden)
        or value.source_entry_count <= 0
        or value.source_entry_count != len(value.source_entry_hashes)
        or value.source_entry_count != len(value.source_subsystem_keys)
        or value.engine_id != ENGINE_ID
        or value.schema_version != SCHEMA_VERSION
        or value.algorithm_version != ALGORITHM_VERSION
        or value.attestation_status != ATTESTATION_STATUS
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(
            "INT-OII-016 permanent safety boundary violated"
        )
    return True


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ATTESTATION_STATUS",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation",
    "attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation",
    "verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation",
]
