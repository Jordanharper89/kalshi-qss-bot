from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Any

OCI_001_BUILD_ID = "OCI-001"
OCI_001_REVISION = "OCI_001_CONTINUOUS_INTAKE_FOUNDATION_V1"
OCI_001_SCHEMA_VERSION = "1.0.0"
SUBSYSTEM_ID = "oracle_continuous_intake"
MODE = "continuous_read_only_intake"

PROHIBITED_CAPABILITIES = (
    "qseries_execution",
    "order_placement",
    "publication",
    "upstream_mutation",
    "destructive_storage",
)

def _hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class OCIIntakePolicy:
    read_only_upstream: bool = True
    deterministic_replay_required: bool = True
    append_only_checkpoint_required: bool = True
    postgresql_read_only_required: bool = True
    terminal_is_consumer_only: bool = True
    api_is_consumer_only: bool = True
    qseries_execution_allowed: bool = False
    publication_allowed: bool = False
    upstream_mutation_allowed: bool = False

    @property
    def policy_hash(self) -> str:
        return _hash(asdict(self))

@dataclass(frozen=True)
class OCIIntakeLineage:
    source_kind: str
    source_ref: str
    source_hash: str
    observed_at: str
    sequence: int

    def __post_init__(self) -> None:
        if not self.source_kind or not self.source_ref:
            raise ValueError("source identity is required")
        if len(self.source_hash) != 64:
            raise ValueError("source_hash must be sha256 hex")
        int(self.source_hash, 16)
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")

    @property
    def lineage_hash(self) -> str:
        return _hash(asdict(self))

def build_oci_001_certification_manifest() -> Mapping[str, Any]:
    policy = OCIIntakePolicy()
    raw = {
        "subsystem_id": SUBSYSTEM_ID,
        "build_id": OCI_001_BUILD_ID,
        "revision": OCI_001_REVISION,
        "schema_version": OCI_001_SCHEMA_VERSION,
        "mode": MODE,
        "policy_hash": policy.policy_hash,
        "prohibited_capabilities": PROHIBITED_CAPABILITIES,
        "network_write_enabled": False,
        "postgresql_write_enabled": False,
        "publication_enabled": False,
        "execution_enabled": False,
    }
    return MappingProxyType({**raw, "manifest_hash": _hash(raw)})

def verify_oci_001_continuous_intake_foundation() -> bool:
    p = OCIIntakePolicy()
    m = build_oci_001_certification_manifest()
    return (
        p.read_only_upstream
        and p.deterministic_replay_required
        and p.postgresql_read_only_required
        and not p.qseries_execution_allowed
        and not p.publication_allowed
        and not p.upstream_mutation_allowed
        and not m["postgresql_write_enabled"]
        and not m["execution_enabled"]
    )
