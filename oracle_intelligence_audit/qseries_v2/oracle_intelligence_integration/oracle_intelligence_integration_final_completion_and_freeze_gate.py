from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation,
    verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation,
)

ENGINE_ID = "INT-OII-017"
SCHEMA_VERSION = "INT-OII-017.v1"
ALGORITHM_VERSION = "oracle-intelligence-integration-final-completion-and-freeze.v1"
COMPLETION_STATUS = "oracle_intelligence_integration_complete_and_frozen"


class OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(ValueError):
    pass


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _stable_hash(value: object) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OracleIntelligenceIntegrationFinalCompletionAndFreeze:
    completion_id: str
    source_attestation_id: str
    source_attestation_hash: str
    source_continuation_id: str
    source_continuation_hash: str
    source_session_id: str
    source_session_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    continuation_attestation_verified: bool
    complete_lineage_verified: bool
    deterministic_completion: bool
    immutable_freeze: bool
    integration_complete: bool
    further_int_oii_certification_required: bool
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
    completion_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    completion_hash: str


def complete_and_freeze_oracle_intelligence_integration(
    *, attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation
) -> OracleIntelligenceIntegrationFinalCompletionAndFreeze:
    try:
        verified = verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation(attestation)
    except Exception as exc:
        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(
            "INT-OII-016 continuation attestation verification failed"
        ) from exc
    if verified is not True:
        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(
            "INT-OII-016 continuation attestation was not verified"
        )
    if (
        attestation.source_entry_count <= 0
        or attestation.source_entry_count != len(attestation.source_entry_hashes)
        or attestation.source_entry_count != len(attestation.source_subsystem_keys)
    ):
        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(
            "certified integration scope mismatch"
        )
    required = (
        attestation.continuation_verified,
        attestation.deterministic_attestation,
        attestation.bounded_attestation_scope,
        attestation.single_continuation_scope,
        attestation.attestation_single_use,
        attestation.downstream_read_only_consumption_active,
        attestation.read_only,
    )
    forbidden = (
        attestation.duplicate_attestation_allowed,
        attestation.attestation_reversible,
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
    if not all(required) or any(forbidden):
        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(
            "INT-OII-016 read-only boundary mismatch"
        )
    body = {
        "source_attestation_id": attestation.attestation_id,
        "source_attestation_hash": attestation.attestation_hash,
        "source_continuation_id": attestation.source_continuation_id,
        "source_continuation_hash": attestation.source_continuation_hash,
        "source_session_id": attestation.source_session_id,
        "source_session_hash": attestation.source_session_hash,
        "source_registry_id": attestation.source_registry_id,
        "source_registry_hash": attestation.source_registry_hash,
        "source_entry_count": attestation.source_entry_count,
        "source_entry_hashes": tuple(attestation.source_entry_hashes),
        "source_subsystem_keys": tuple(attestation.source_subsystem_keys),
        "continuation_attestation_verified": True,
        "complete_lineage_verified": True,
        "deterministic_completion": True,
        "immutable_freeze": True,
        "integration_complete": True,
        "further_int_oii_certification_required": False,
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
        "completion_status": COMPLETION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    completion_hash = _stable_hash(body)
    return OracleIntelligenceIntegrationFinalCompletionAndFreeze(
        completion_id="int-oii-completion:" + completion_hash,
        completion_hash=completion_hash,
        **body,
    )


def verify_oracle_intelligence_integration_final_completion_and_freeze(
    value: OracleIntelligenceIntegrationFinalCompletionAndFreeze,
) -> bool:
    if not isinstance(value, OracleIntelligenceIntegrationFinalCompletionAndFreeze):
        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError("unexpected completion record type")
    body = asdict(value)
    completion_hash = body.pop("completion_hash")
    completion_id = body.pop("completion_id")
    expected_hash = _stable_hash(body)
    if completion_hash != expected_hash or completion_id != "int-oii-completion:" + expected_hash:
        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError("completion identity mismatch")
    required = (
        value.continuation_attestation_verified,
        value.complete_lineage_verified,
        value.deterministic_completion,
        value.immutable_freeze,
        value.integration_complete,
        value.downstream_read_only_consumption_active,
        value.read_only,
    )
    forbidden = (
        value.further_int_oii_certification_required,
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
        or value.completion_status != COMPLETION_STATUS
    ):
        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(
            "INT-OII-017 permanent completion boundary violated"
        )
    return True


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "COMPLETION_STATUS",
    "OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError",
    "OracleIntelligenceIntegrationFinalCompletionAndFreeze",
    "complete_and_freeze_oracle_intelligence_integration",
    "verify_oracle_intelligence_integration_final_completion_and_freeze",
]
