from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption,
    verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption,
)

ENGINE_ID = "INT-OII-015"
SCHEMA_VERSION = "INT-OII-015.v1"
ALGORITHM_VERSION = "oracle-certified-intelligence-read-only-consumption-session-activation-continuation.v1"
CONTINUATION_STATUS = "oracle_certified_intelligence_read_only_consumption_session_activation_continued"

class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(ValueError):
    pass

def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def _stable_hash(value: object) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation:
    continuation_id: str
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
    authorization_consumption_verified: bool
    deterministic_continuation: bool
    bounded_continuation_scope: bool
    single_consumption_scope: bool
    continuation_single_use: bool
    duplicate_continuation_allowed: bool
    continuation_reversible: bool
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
    continuation_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    continuation_hash: str

def continue_oracle_certified_intelligence_read_only_consumption_session_activation(*, consumption: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation:
    try:
        verified = verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption(consumption)
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError("INT-OII-014 authorization consumption verification failed") from exc
    if verified is not True:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError("INT-OII-014 authorization consumption was not verified")
    if consumption.source_entry_count <= 0 or consumption.source_entry_count != len(consumption.source_entry_hashes) or consumption.source_entry_count != len(consumption.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError("certified subsystem scope mismatch")
    required = (consumption.activation_authorization_verified, consumption.deterministic_consumption, consumption.bounded_consumption_scope, consumption.single_authorization_scope, consumption.single_use_authorization_consumed, consumption.downstream_read_only_consumption_active, consumption.read_only)
    forbidden = (consumption.duplicate_consumption_allowed, consumption.consumption_reversible, consumption.registry_mutation_allowed, consumption.oracle_execution_allowed, consumption.reasoning_execution_allowed, consumption.probability_estimation_allowed, consumption.final_intelligence_conclusion_allowed, consumption.publication_allowed, consumption.alerting_allowed, consumption.qseries_handoff_allowed, consumption.qseries_execution_allowed, consumption.order_creation_allowed, consumption.funds_movement_allowed, consumption.portfolio_mutation_allowed)
    if not all(required) or any(forbidden):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError("INT-OII-014 read-only boundary mismatch")
    body = {
        "source_authorization_consumption_id": consumption.consumption_id,
        "source_authorization_consumption_hash": consumption.consumption_hash,
        "source_activation_authorization_id": consumption.source_activation_authorization_id,
        "source_activation_authorization_hash": consumption.source_activation_authorization_hash,
        "source_activation_id": consumption.source_activation_id,
        "source_activation_hash": consumption.source_activation_hash,
        "source_session_id": consumption.source_session_id,
        "source_session_hash": consumption.source_session_hash,
        "source_registry_id": consumption.source_registry_id,
        "source_registry_hash": consumption.source_registry_hash,
        "source_entry_count": consumption.source_entry_count,
        "source_entry_hashes": tuple(consumption.source_entry_hashes),
        "source_subsystem_keys": tuple(consumption.source_subsystem_keys),
        "authorization_consumption_verified": True,
        "deterministic_continuation": True,
        "bounded_continuation_scope": True,
        "single_consumption_scope": True,
        "continuation_single_use": True,
        "duplicate_continuation_allowed": False,
        "continuation_reversible": False,
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
        "continuation_status": CONTINUATION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    h = _stable_hash(body)
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation(continuation_id="oracle-certified-intelligence-read-only-consumption-session-activation-continuation:" + h, **body, continuation_hash=h)

def verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(value: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation) -> bool:
    body = asdict(value)
    supplied = body.pop("continuation_hash")
    continuation_id = body.pop("continuation_id")
    expected = _stable_hash(body)
    if supplied != expected or continuation_id != "oracle-certified-intelligence-read-only-consumption-session-activation-continuation:" + expected:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError("continuation hash mismatch")
    required = (value.authorization_consumption_verified, value.deterministic_continuation, value.bounded_continuation_scope, value.single_consumption_scope, value.continuation_single_use, value.downstream_read_only_consumption_active, value.read_only)
    forbidden = (value.duplicate_continuation_allowed, value.continuation_reversible, value.registry_mutation_allowed, value.oracle_execution_allowed, value.reasoning_execution_allowed, value.probability_estimation_allowed, value.final_intelligence_conclusion_allowed, value.publication_allowed, value.alerting_allowed, value.qseries_handoff_allowed, value.qseries_execution_allowed, value.order_creation_allowed, value.funds_movement_allowed, value.portfolio_mutation_allowed)
    if not all(required) or any(forbidden) or value.engine_id != ENGINE_ID or value.schema_version != SCHEMA_VERSION or value.algorithm_version != ALGORITHM_VERSION or value.continuation_status != CONTINUATION_STATUS:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError("INT-OII-015 permanent safety boundary violated")
    return True

__all__ = ["ENGINE_ID", "SCHEMA_VERSION", "ALGORITHM_VERSION", "CONTINUATION_STATUS", "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError", "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation", "continue_oracle_certified_intelligence_read_only_consumption_session_activation", "verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation"]
