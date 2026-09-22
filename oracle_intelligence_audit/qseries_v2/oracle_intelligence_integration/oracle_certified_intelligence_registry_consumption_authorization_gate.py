from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_attestation_gate import (
    OracleCertifiedIntelligenceRegistryAttestation,
    verify_oracle_certified_intelligence_registry_attestation,
)

ENGINE_ID = "INT-OII-003"
SCHEMA_VERSION = "INT-OII-003.v1"
ALGORITHM_VERSION = "oracle-certified-intelligence-registry-consumption-authorization.v1"
AUTHORIZATION_STATUS = "oracle_certified_intelligence_registry_consumption_authorized"


class OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(ValueError):
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
class OracleCertifiedIntelligenceRegistryConsumptionAuthorization:
    authorization_id: str
    source_attestation_id: str
    source_attestation_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    attestation_verified: bool
    exact_attestation_hash_scope_preserved: bool
    exact_registry_hash_scope_preserved: bool
    exact_entry_hash_scope_preserved: bool
    certified_subsystem_scope_preserved: bool
    read_only_consumption_authorized: bool
    deterministic_consumption_required: bool
    bounded_registry_scope_required: bool
    single_use_authorization_required: bool
    authorization_consumed: bool
    registry_mutation_allowed: bool
    oracle_execution_allowed: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    read_only: bool
    authorization_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    authorization_hash: str


def authorize_oracle_certified_intelligence_registry_consumption(
    *,
    attestation: OracleCertifiedIntelligenceRegistryAttestation,
) -> OracleCertifiedIntelligenceRegistryConsumptionAuthorization:
    try:
        verdict = verify_oracle_certified_intelligence_registry_attestation(
            attestation
        )
    except Exception as exc:
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "INT-OII-002 registry attestation verification failed"
        ) from exc

    if verdict is False:
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "INT-OII-002 registry attestation verifier returned false"
        )

    if attestation.source_entry_count <= 0:
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "attested registry must contain at least one subsystem"
        )

    if attestation.source_entry_count != len(attestation.source_entry_hashes):
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "attested entry hash scope mismatch"
        )

    if attestation.source_entry_count != len(attestation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "attested subsystem scope mismatch"
        )

    body = {
        "source_attestation_id": attestation.attestation_id,
        "source_attestation_hash": attestation.attestation_hash,
        "source_registry_id": attestation.source_registry_id,
        "source_registry_hash": attestation.source_registry_hash,
        "source_entry_count": attestation.source_entry_count,
        "source_entry_hashes": attestation.source_entry_hashes,
        "source_subsystem_keys": attestation.source_subsystem_keys,
        "attestation_verified": True,
        "exact_attestation_hash_scope_preserved": True,
        "exact_registry_hash_scope_preserved": True,
        "exact_entry_hash_scope_preserved": True,
        "certified_subsystem_scope_preserved": True,
        "read_only_consumption_authorized": True,
        "deterministic_consumption_required": True,
        "bounded_registry_scope_required": True,
        "single_use_authorization_required": True,
        "authorization_consumed": False,
        "registry_mutation_allowed": False,
        "oracle_execution_allowed": False,
        "publication_allowed": False,
        "alerting_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "read_only": True,
        "authorization_status": AUTHORIZATION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }

    authorization_hash = stable_hash(body)

    return OracleCertifiedIntelligenceRegistryConsumptionAuthorization(
        authorization_id=(
            "oracle-certified-intelligence-registry-consumption-authorization:"
            + authorization_hash
        ),
        **body,
        authorization_hash=authorization_hash,
    )


def verify_oracle_certified_intelligence_registry_consumption_authorization(
    authorization: OracleCertifiedIntelligenceRegistryConsumptionAuthorization,
) -> bool:
    if not isinstance(
        authorization,
        OracleCertifiedIntelligenceRegistryConsumptionAuthorization,
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "invalid registry consumption authorization"
        )

    body = {
        key: value
        for key, value in asdict(authorization).items()
        if key not in {"authorization_id", "authorization_hash"}
    }
    expected_hash = stable_hash(body)

    if authorization.authorization_hash != expected_hash:
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "registry consumption authorization hash mismatch"
        )

    if authorization.authorization_id != (
        "oracle-certified-intelligence-registry-consumption-authorization:"
        + expected_hash
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "registry consumption authorization identity mismatch"
        )

    if authorization.source_entry_count != len(
        authorization.source_entry_hashes
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "authorized entry hash scope mismatch"
        )

    if authorization.source_entry_count != len(
        authorization.source_subsystem_keys
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "authorized subsystem scope mismatch"
        )

    if authorization.source_subsystem_keys != tuple(
        sorted(authorization.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "authorized subsystem scope is not deterministic"
        )

    if len(authorization.source_subsystem_keys) != len(
        set(authorization.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "authorized subsystem scope contains duplicates"
        )

    forbidden = (
        authorization.authorization_consumed,
        authorization.registry_mutation_allowed,
        authorization.oracle_execution_allowed,
        authorization.publication_allowed,
        authorization.alerting_allowed,
        authorization.qseries_handoff_allowed,
        authorization.qseries_execution_allowed,
        authorization.order_creation_allowed,
        authorization.funds_movement_allowed,
        authorization.portfolio_mutation_allowed,
    )

    if (
        authorization.engine_id != ENGINE_ID
        or authorization.schema_version != SCHEMA_VERSION
        or authorization.algorithm_version != ALGORITHM_VERSION
        or authorization.authorization_status != AUTHORIZATION_STATUS
        or authorization.source_entry_count <= 0
        or authorization.attestation_verified is not True
        or authorization.exact_attestation_hash_scope_preserved is not True
        or authorization.exact_registry_hash_scope_preserved is not True
        or authorization.exact_entry_hash_scope_preserved is not True
        or authorization.certified_subsystem_scope_preserved is not True
        or authorization.read_only_consumption_authorized is not True
        or authorization.deterministic_consumption_required is not True
        or authorization.bounded_registry_scope_required is not True
        or authorization.single_use_authorization_required is not True
        or authorization.read_only is not True
        or any(forbidden)
    ):
        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(
            "INT-OII-003 permanent safety boundary violated"
        )

    return True


def serialize_oracle_certified_intelligence_registry_consumption_authorization(
    authorization: OracleCertifiedIntelligenceRegistryConsumptionAuthorization,
) -> str:
    verify_oracle_certified_intelligence_registry_consumption_authorization(
        authorization
    )
    return canonical_json(authorization)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "AUTHORIZATION_STATUS",
    "OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError",
    "OracleCertifiedIntelligenceRegistryConsumptionAuthorization",
    "authorize_oracle_certified_intelligence_registry_consumption",
    "verify_oracle_certified_intelligence_registry_consumption_authorization",
    "serialize_oracle_certified_intelligence_registry_consumption_authorization",
]
