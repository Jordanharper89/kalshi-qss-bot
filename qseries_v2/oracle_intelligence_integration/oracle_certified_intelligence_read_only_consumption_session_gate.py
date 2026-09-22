from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_activation_attestation_gate import (
    OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation,
    verify_oracle_certified_intelligence_registry_consumption_activation_attestation,
)

ENGINE_ID = "INT-OII-006"
SCHEMA_VERSION = "INT-OII-006.v1"
ALGORITHM_VERSION = "oracle-certified-intelligence-read-only-consumption-session.v1"
SESSION_STATUS = "oracle_certified_intelligence_read_only_consumption_session_materialized"


class OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(ValueError):
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
class OracleCertifiedIntelligenceReadOnlyConsumptionSession:
    session_id: str
    source_activation_attestation_id: str
    source_activation_attestation_hash: str
    source_activation_id: str
    source_activation_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    activation_attestation_verified: bool
    exact_activation_attestation_hash_scope_preserved: bool
    exact_activation_hash_scope_preserved: bool
    exact_authorization_hash_scope_preserved: bool
    exact_registry_hash_scope_preserved: bool
    exact_entry_hash_scope_preserved: bool
    certified_subsystem_scope_preserved: bool
    deterministic_session_identity: bool
    bounded_session_scope: bool
    single_activation_scope: bool
    session_materialized: bool
    session_active: bool
    session_closed: bool
    read_only_consumption_allowed: bool
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
    session_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    session_hash: str


def materialize_oracle_certified_intelligence_read_only_consumption_session(
    *,
    activation_attestation: OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation,
) -> OracleCertifiedIntelligenceReadOnlyConsumptionSession:
    try:
        verdict = (
            verify_oracle_certified_intelligence_registry_consumption_activation_attestation(
                activation_attestation
            )
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "INT-OII-005 activation attestation verification failed"
        ) from exc

    if verdict is False:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "INT-OII-005 activation attestation verifier returned false"
        )

    if activation_attestation.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "certified subsystem scope is empty"
        )

    if activation_attestation.source_entry_count != len(
        activation_attestation.source_entry_hashes
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "entry hash scope mismatch"
        )

    if activation_attestation.source_entry_count != len(
        activation_attestation.source_subsystem_keys
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "subsystem scope mismatch"
        )

    body = {
        "source_activation_attestation_id": activation_attestation.attestation_id,
        "source_activation_attestation_hash": activation_attestation.attestation_hash,
        "source_activation_id": activation_attestation.source_activation_id,
        "source_activation_hash": activation_attestation.source_activation_hash,
        "source_authorization_id": activation_attestation.source_authorization_id,
        "source_authorization_hash": activation_attestation.source_authorization_hash,
        "source_registry_id": activation_attestation.source_registry_id,
        "source_registry_hash": activation_attestation.source_registry_hash,
        "source_entry_count": activation_attestation.source_entry_count,
        "source_entry_hashes": activation_attestation.source_entry_hashes,
        "source_subsystem_keys": activation_attestation.source_subsystem_keys,
        "activation_attestation_verified": True,
        "exact_activation_attestation_hash_scope_preserved": True,
        "exact_activation_hash_scope_preserved": True,
        "exact_authorization_hash_scope_preserved": True,
        "exact_registry_hash_scope_preserved": True,
        "exact_entry_hash_scope_preserved": True,
        "certified_subsystem_scope_preserved": True,
        "deterministic_session_identity": True,
        "bounded_session_scope": True,
        "single_activation_scope": True,
        "session_materialized": True,
        "session_active": True,
        "session_closed": False,
        "read_only_consumption_allowed": True,
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
        "session_status": SESSION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }

    session_hash = stable_hash(body)

    return OracleCertifiedIntelligenceReadOnlyConsumptionSession(
        session_id="oracle-certified-intelligence-read-only-consumption-session:"
        + session_hash,
        **body,
        session_hash=session_hash,
    )


def verify_oracle_certified_intelligence_read_only_consumption_session(
    session: OracleCertifiedIntelligenceReadOnlyConsumptionSession,
) -> bool:
    if not isinstance(
        session,
        OracleCertifiedIntelligenceReadOnlyConsumptionSession,
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "invalid read-only consumption session"
        )

    body = {
        key: value
        for key, value in asdict(session).items()
        if key not in {"session_id", "session_hash"}
    }
    expected_hash = stable_hash(body)

    if session.session_hash != expected_hash:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "session hash mismatch"
        )

    if session.session_id != (
        "oracle-certified-intelligence-read-only-consumption-session:"
        + expected_hash
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "session identity mismatch"
        )

    if session.source_entry_count != len(session.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "session entry hash scope mismatch"
        )

    if session.source_entry_count != len(session.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "session subsystem scope mismatch"
        )

    if session.source_subsystem_keys != tuple(
        sorted(session.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "session subsystem scope is not deterministic"
        )

    if len(session.source_subsystem_keys) != len(
        set(session.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "session subsystem scope contains duplicates"
        )

    required_true = (
        session.activation_attestation_verified,
        session.exact_activation_attestation_hash_scope_preserved,
        session.exact_activation_hash_scope_preserved,
        session.exact_authorization_hash_scope_preserved,
        session.exact_registry_hash_scope_preserved,
        session.exact_entry_hash_scope_preserved,
        session.certified_subsystem_scope_preserved,
        session.deterministic_session_identity,
        session.bounded_session_scope,
        session.single_activation_scope,
        session.session_materialized,
        session.session_active,
        session.read_only_consumption_allowed,
        session.read_only,
    )

    forbidden = (
        session.session_closed,
        session.registry_mutation_allowed,
        session.oracle_execution_allowed,
        session.reasoning_execution_allowed,
        session.probability_estimation_allowed,
        session.final_intelligence_conclusion_allowed,
        session.publication_allowed,
        session.alerting_allowed,
        session.qseries_handoff_allowed,
        session.qseries_execution_allowed,
        session.order_creation_allowed,
        session.funds_movement_allowed,
        session.portfolio_mutation_allowed,
    )

    if (
        session.engine_id != ENGINE_ID
        or session.schema_version != SCHEMA_VERSION
        or session.algorithm_version != ALGORITHM_VERSION
        or session.session_status != SESSION_STATUS
        or session.source_entry_count <= 0
        or not all(value is True for value in required_true)
        or any(forbidden)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(
            "INT-OII-006 permanent safety boundary violated"
        )

    return True


def serialize_oracle_certified_intelligence_read_only_consumption_session(
    session: OracleCertifiedIntelligenceReadOnlyConsumptionSession,
) -> str:
    verify_oracle_certified_intelligence_read_only_consumption_session(session)
    return canonical_json(session)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "SESSION_STATUS",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSession",
    "materialize_oracle_certified_intelligence_read_only_consumption_session",
    "verify_oracle_certified_intelligence_read_only_consumption_session",
    "serialize_oracle_certified_intelligence_read_only_consumption_session",
]
