from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_assembly_gate import (
    OracleCertifiedIntelligenceRegistry,
    verify_oracle_certified_intelligence_registry,
)

ENGINE_ID = "INT-OII-002"
SCHEMA_VERSION = "INT-OII-002.v1"
ALGORITHM_VERSION = "oracle-certified-intelligence-registry-attestation.v1"
ATTESTATION_STATUS = "oracle_certified_intelligence_registry_attested"


class OracleCertifiedIntelligenceRegistryAttestationInvariantError(ValueError):
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
class OracleCertifiedIntelligenceRegistryAttestation:
    attestation_id: str
    source_registry_id: str
    source_registry_hash: str
    source_entry_count: int
    source_entry_hashes: tuple[str, ...]
    source_subsystem_keys: tuple[str, ...]
    registry_verified: bool
    exact_registry_hash_scope_preserved: bool
    exact_entry_hash_scope_preserved: bool
    deterministic_registration_order_verified: bool
    duplicate_subsystem_rejection_verified: bool
    immutable_registry_verified: bool
    downstream_read_only_consumption_verified: bool
    registry_mutation_allowed: bool
    oracle_execution_allowed: bool
    publication_allowed: bool
    alerting_allowed: bool
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


def attest_oracle_certified_intelligence_registry(
    *,
    registry: OracleCertifiedIntelligenceRegistry,
) -> OracleCertifiedIntelligenceRegistryAttestation:
    try:
        verdict = verify_oracle_certified_intelligence_registry(registry)
    except Exception as exc:
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "INT-OII-001 registry verification failed"
        ) from exc

    if verdict is False:
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "INT-OII-001 registry verifier returned false"
        )

    if registry.entry_count <= 0:
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "registry must contain at least one certified subsystem"
        )

    entry_hashes = tuple(entry.entry_hash for entry in registry.entries)
    subsystem_keys = tuple(entry.subsystem_key for entry in registry.entries)

    if subsystem_keys != tuple(sorted(subsystem_keys)):
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "registry subsystem order is not deterministic"
        )
    if len(subsystem_keys) != len(set(subsystem_keys)):
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "registry contains duplicate subsystem keys"
        )

    body = {
        "source_registry_id": registry.registry_id,
        "source_registry_hash": registry.registry_hash,
        "source_entry_count": registry.entry_count,
        "source_entry_hashes": entry_hashes,
        "source_subsystem_keys": subsystem_keys,
        "registry_verified": True,
        "exact_registry_hash_scope_preserved": True,
        "exact_entry_hash_scope_preserved": True,
        "deterministic_registration_order_verified": True,
        "duplicate_subsystem_rejection_verified": True,
        "immutable_registry_verified": True,
        "downstream_read_only_consumption_verified": True,
        "registry_mutation_allowed": False,
        "oracle_execution_allowed": False,
        "publication_allowed": False,
        "alerting_allowed": False,
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

    return OracleCertifiedIntelligenceRegistryAttestation(
        attestation_id="oracle-certified-intelligence-registry-attestation:"
        + attestation_hash,
        **body,
        attestation_hash=attestation_hash,
    )


def verify_oracle_certified_intelligence_registry_attestation(
    attestation: OracleCertifiedIntelligenceRegistryAttestation,
) -> bool:
    if not isinstance(
        attestation,
        OracleCertifiedIntelligenceRegistryAttestation,
    ):
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "invalid registry attestation record"
        )

    body = {
        key: value
        for key, value in asdict(attestation).items()
        if key not in {"attestation_id", "attestation_hash"}
    }
    expected_hash = stable_hash(body)

    if attestation.attestation_hash != expected_hash:
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "registry attestation hash mismatch"
        )
    if attestation.attestation_id != (
        "oracle-certified-intelligence-registry-attestation:" + expected_hash
    ):
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "registry attestation identity mismatch"
        )

    if attestation.source_entry_count != len(attestation.source_entry_hashes):
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "entry count and entry hash scope mismatch"
        )
    if attestation.source_entry_count != len(attestation.source_subsystem_keys):
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "entry count and subsystem scope mismatch"
        )
    if attestation.source_subsystem_keys != tuple(
        sorted(attestation.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "attested subsystem order mismatch"
        )
    if len(attestation.source_subsystem_keys) != len(
        set(attestation.source_subsystem_keys)
    ):
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "attested subsystem scope contains duplicates"
        )

    forbidden = (
        attestation.registry_mutation_allowed,
        attestation.oracle_execution_allowed,
        attestation.publication_allowed,
        attestation.alerting_allowed,
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
        or attestation.registry_verified is not True
        or attestation.exact_registry_hash_scope_preserved is not True
        or attestation.exact_entry_hash_scope_preserved is not True
        or attestation.deterministic_registration_order_verified is not True
        or attestation.duplicate_subsystem_rejection_verified is not True
        or attestation.immutable_registry_verified is not True
        or attestation.downstream_read_only_consumption_verified is not True
        or attestation.read_only is not True
        or any(forbidden)
    ):
        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(
            "INT-OII-002 permanent safety boundary violated"
        )

    return True


def serialize_oracle_certified_intelligence_registry_attestation(
    attestation: OracleCertifiedIntelligenceRegistryAttestation,
) -> str:
    verify_oracle_certified_intelligence_registry_attestation(attestation)
    return canonical_json(attestation)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ATTESTATION_STATUS",
    "OracleCertifiedIntelligenceRegistryAttestationInvariantError",
    "OracleCertifiedIntelligenceRegistryAttestation",
    "attest_oracle_certified_intelligence_registry",
    "verify_oracle_certified_intelligence_registry_attestation",
    "serialize_oracle_certified_intelligence_registry_attestation",
]
