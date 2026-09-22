from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSession,
    verify_oracle_certified_intelligence_read_only_consumption_session,
)

ENGINE_ID = "INT-OII-007"
SCHEMA_VERSION = "INT-OII-007.v1"
ALGORITHM_VERSION = (
    "oracle-certified-intelligence-read-only-consumption-session-attestation.v1"
)
ATTESTATION_STATUS = (
    "oracle_certified_intelligence_read_only_consumption_session_attested"
)


class OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
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
class OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation:
    attestation_id: str
    source_session_id: str
    source_session_hash: str
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
    session_verified: bool
    exact_session_hash_scope_preserved: bool
    exact_activation_attestation_hash_scope_preserved: bool
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


def attest_oracle_certified_intelligence_read_only_consumption_session(
    *,
    session: OracleCertifiedIntelligenceReadOnlyConsumptionSession,
) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation:
    try:
        verdict = verify_oracle_certified_intelligence_read_only_consumption_session(
            session
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "INT-OII-006 read-only consumption session verification failed"
        ) from exc

    if verdict is False:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "INT-OII-006 session verifier returned false"
        )

    if session.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "certified subsystem scope is empty"
        )

    if session.source_entry_count != len(session.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "entry hash scope mismatch"
        )

    if session.source_entry_count != len(session.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "subsystem scope mismatch"
        )

    body = {
        "source_session_id": session.session_id,
        "source_session_hash": session.session_hash,
        "source_activation_attestation_id": (
            session.source_activation_attestation_id
        ),
        "source_activation_attestation_hash": (
            session.source_activation_attestation_hash
        ),
        "source_activation_id": session.source_activation_id,
        "source_activation_hash": session.source_activation_hash,
        "source_authorization_id": session.source_authorization_id,
        "source_authorization_hash": session.source_authorization_hash,
        "source_registry_id": session.source_registry_id,
        "source_registry_hash": session.source_registry_hash,
        "source_entry_count": session.source_entry_count,
        "source_entry_hashes": session.source_entry_hashes,
        "source_subsystem_keys": session.source_subsystem_keys,
        "session_verified": True,
        "exact_session_hash_scope_preserved": True,
        "exact_activation_attestation_hash_scope_preserved": True,
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

    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation(
        attestation_id=(
            "oracle-certified-intelligence-read-only-consumption-session-attestation:"
            + attestation_hash
        ),
        **body,
        attestation_hash=attestation_hash,
    )


def verify_oracle_certified_intelligence_read_only_consumption_session_attestation(
    attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,
) -> bool:
    if not isinstance(
        attestation,
        OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "invalid read-only consumption session attestation"
        )

    body = {
        key: value
        for key, value in asdict(attestation).items()
        if key not in {"attestation_id", "attestation_hash"}
    }
    expected_hash = stable_hash(body)

    if attestation.attestation_hash != expected_hash:
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "session attestation hash mismatch"
        )

    if attestation.attestation_id != (
        "oracle-certified-intelligence-read-only-consumption-session-attestation:"
        + expected_hash
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "session attestation identity mismatch"
        )

    if attestation.source_entry_count != len(attestation.source_entry_hashes):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "attested entry hash scope mismatch"
        )

    if attestation.source_entry_count != len(attestation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "attested subsystem scope mismatch"
        )

    if attestation.source_subsystem_keys != tuple(
        sorted(attestation.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "attested subsystem scope is not deterministic"
        )

    if len(attestation.source_subsystem_keys) != len(
        set(attestation.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "attested subsystem scope contains duplicates"
        )

    required_true = (
        attestation.session_verified,
        attestation.exact_session_hash_scope_preserved,
        attestation.exact_activation_attestation_hash_scope_preserved,
        attestation.exact_activation_hash_scope_preserved,
        attestation.exact_authorization_hash_scope_preserved,
        attestation.exact_registry_hash_scope_preserved,
        attestation.exact_entry_hash_scope_preserved,
        attestation.certified_subsystem_scope_preserved,
        attestation.deterministic_session_identity_verified,
        attestation.bounded_session_scope_verified,
        attestation.single_activation_scope_verified,
        attestation.session_materialization_verified,
        attestation.active_session_verified,
        attestation.unclosed_session_verified,
        attestation.read_only_consumption_verified,
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
        attestation.engine_id != ENGINE_ID
        or attestation.schema_version != SCHEMA_VERSION
        or attestation.algorithm_version != ALGORITHM_VERSION
        or attestation.attestation_status != ATTESTATION_STATUS
        or attestation.source_entry_count <= 0
        or not all(value is True for value in required_true)
        or any(forbidden)
    ):
        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(
            "INT-OII-007 permanent safety boundary violated"
        )

    return True


def serialize_oracle_certified_intelligence_read_only_consumption_session_attestation(
    attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,
) -> str:
    verify_oracle_certified_intelligence_read_only_consumption_session_attestation(
        attestation
    )
    return canonical_json(attestation)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ATTESTATION_STATUS",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError",
    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation",
    "attest_oracle_certified_intelligence_read_only_consumption_session",
    "verify_oracle_certified_intelligence_read_only_consumption_session_attestation",
    "serialize_oracle_certified_intelligence_read_only_consumption_session_attestation",
]
