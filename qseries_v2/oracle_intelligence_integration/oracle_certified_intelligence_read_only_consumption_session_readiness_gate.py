from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_attestation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,
    verify_oracle_certified_intelligence_read_only_consumption_session_attestation,
)

ENGINE_ID = "INT-OII-008"
SCHEMA_VERSION = "INT-OII-008.v1"
ALGORITHM_VERSION = (
    "oracle-certified-intelligence-read-only-consumption-session-readiness.v1"
)
READINESS_STATUS = (
    "oracle_certified_intelligence_read_only_consumption_session_ready"
)


class OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
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
class OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness:
    readiness_id: str
    source_session_attestation_id: str
    source_session_attestation_hash: str
    source_session_id: str
    source_session_hash: str
    source_activation_id: str
    source_activation_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    session_attestation_verified: bool
    exact_session_attestation_hash_scope_preserved: bool
    exact_session_hash_scope_preserved: bool
    exact_activation_hash_scope_preserved: bool
    exact_authorization_hash_scope_preserved: bool
    exact_registry_hash_scope_preserved: bool
    exact_entry_hash_scope_preserved: bool
    certified_subsystem_scope_preserved: bool
    deterministic_session_identity_verified: bool
    bounded_session_scope_verified: bool
    single_activation_scope_verified: bool
    session_materialization_verified: bool
    active_session_verified: bool
    unclosed_session_verified: bool
    read_only_consumption_verified: bool
    downstream_read_only_consumption_ready: bool
    readiness_single_scope: bool
    readiness_reversible: bool
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
    readiness_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    readiness_hash: str


def certify_oracle_certified_intelligence_read_only_consumption_session_readiness(
    *,
    session_attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,
) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness:
    try:
        verdict = (
            verify_oracle_certified_intelligence_read_only_consumption_session_attestation(
                session_attestation
            )
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "INT-OII-007 session attestation verification failed"
        ) from exc

    if verdict is False:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "INT-OII-007 session attestation verifier returned false"
        )

    if session_attestation.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "certified subsystem scope is empty"
        )

    if session_attestation.source_entry_count != len(
        session_attestation.source_entry_hashes
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "entry hash scope mismatch"
        )

    if session_attestation.source_entry_count != len(
        session_attestation.source_subsystem_keys
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "subsystem scope mismatch"
        )

    body = {
        "source_session_attestation_id": session_attestation.attestation_id,
        "source_session_attestation_hash": session_attestation.attestation_hash,
        "source_session_id": session_attestation.source_session_id,
        "source_session_hash": session_attestation.source_session_hash,
        "source_activation_id": session_attestation.source_activation_id,
        "source_activation_hash": session_attestation.source_activation_hash,
        "source_authorization_id": session_attestation.source_authorization_id,
        "source_authorization_hash": session_attestation.source_authorization_hash,
        "source_registry_id": session_attestation.source_registry_id,
        "source_registry_hash": session_attestation.source_registry_hash,
        "source_entry_count": session_attestation.source_entry_count,
        "source_entry_hashes": session_attestation.source_entry_hashes,
        "source_subsystem_keys": session_attestation.source_subsystem_keys,
        "session_attestation_verified": True,
        "exact_session_attestation_hash_scope_preserved": True,
        "exact_session_hash_scope_preserved": True,
        "exact_activation_hash_scope_preserved": True,
        "exact_authorization_hash_scope_preserved": True,
        "exact_registry_hash_scope_preserved": True,
        "exact_entry_hash_scope_preserved": True,
        "certified_subsystem_scope_preserved": True,
        "deterministic_session_identity_verified": True,
        "bounded_session_scope_verified": True,
        "single_activation_scope_verified": True,
        "session_materialization_verified": True,
        "active_session_verified": True,
        "unclosed_session_verified": True,
        "read_only_consumption_verified": True,
        "downstream_read_only_consumption_ready": True,
        "readiness_single_scope": True,
        "readiness_reversible": False,
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
        "readiness_status": READINESS_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }

    readiness_hash = stable_hash(body)

    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness(
        readiness_id=(
            "oracle-certified-intelligence-read-only-consumption-session-readiness:"
            + readiness_hash
        ),
        **body,
        readiness_hash=readiness_hash,
    )


def verify_oracle_certified_intelligence_read_only_consumption_session_readiness(
    readiness: OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness,
) -> bool:
    if not isinstance(
        readiness,
        OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness,
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "invalid read-only consumption session readiness"
        )

    body = {
        key: value
        for key, value in asdict(readiness).items()
        if key not in {"readiness_id", "readiness_hash"}
    }
    expected_hash = stable_hash(body)

    if readiness.readiness_hash != expected_hash:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "session readiness hash mismatch"
        )

    if readiness.readiness_id != (
        "oracle-certified-intelligence-read-only-consumption-session-readiness:"
        + expected_hash
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "session readiness identity mismatch"
        )

    if readiness.source_entry_count != len(readiness.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "readiness entry hash scope mismatch"
        )

    if readiness.source_entry_count != len(readiness.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "readiness subsystem scope mismatch"
        )

    if readiness.source_subsystem_keys != tuple(
        sorted(readiness.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "readiness subsystem scope is not deterministic"
        )

    if len(readiness.source_subsystem_keys) != len(
        set(readiness.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "readiness subsystem scope contains duplicates"
        )

    required_true = (
        readiness.session_attestation_verified,
        readiness.exact_session_attestation_hash_scope_preserved,
        readiness.exact_session_hash_scope_preserved,
        readiness.exact_activation_hash_scope_preserved,
        readiness.exact_authorization_hash_scope_preserved,
        readiness.exact_registry_hash_scope_preserved,
        readiness.exact_entry_hash_scope_preserved,
        readiness.certified_subsystem_scope_preserved,
        readiness.deterministic_session_identity_verified,
        readiness.bounded_session_scope_verified,
        readiness.single_activation_scope_verified,
        readiness.session_materialization_verified,
        readiness.active_session_verified,
        readiness.unclosed_session_verified,
        readiness.read_only_consumption_verified,
        readiness.downstream_read_only_consumption_ready,
        readiness.readiness_single_scope,
        readiness.read_only,
    )

    forbidden = (
        readiness.readiness_reversible,
        readiness.registry_mutation_allowed,
        readiness.oracle_execution_allowed,
        readiness.reasoning_execution_allowed,
        readiness.probability_estimation_allowed,
        readiness.final_intelligence_conclusion_allowed,
        readiness.publication_allowed,
        readiness.alerting_allowed,
        readiness.qseries_handoff_allowed,
        readiness.qseries_execution_allowed,
        readiness.order_creation_allowed,
        readiness.funds_movement_allowed,
        readiness.portfolio_mutation_allowed,
    )

    if (
        readiness.engine_id != ENGINE_ID
        or readiness.schema_version != SCHEMA_VERSION
        or readiness.algorithm_version != ALGORITHM_VERSION
        or readiness.readiness_status != READINESS_STATUS
        or readiness.source_entry_count <= 0
        or not all(value is True for value in required_true)
        or any(forbidden)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(
            "INT-OII-008 permanent safety boundary violated"
        )

    return True


def serialize_oracle_certified_intelligence_read_only_consumption_session_readiness(
    readiness: OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness,
) -> str:
    verify_oracle_certified_intelligence_read_only_consumption_session_readiness(
        readiness
    )
    return canonical_json(readiness)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "READINESS_STATUS",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness",
    "certify_oracle_certified_intelligence_read_only_consumption_session_readiness",
    "verify_oracle_certified_intelligence_read_only_consumption_session_readiness",
    "serialize_oracle_certified_intelligence_read_only_consumption_session_readiness",
]
