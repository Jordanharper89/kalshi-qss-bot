from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_170_convergence_market_registry import ConvergenceMarketRegistry,verify_umd_170_convergence_market_registry

UMD_171_BUILD_ID="UMD-171"
UMD_171_REVISION="UMD_171_CONVERGENCE_STATE_SNAPSHOT_V1"
UMD_171_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _utc(value:datetime)->datetime:
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True,slots=True)
class ConvergenceStateRecord:
    canonical_market_id:str
    profile_hash:str
    change_types:Tuple[str,...]
    venue_keys:Tuple[str,...]

    def __post_init__(self):
        object.__setattr__(self,"change_types",tuple(self.change_types))
        object.__setattr__(self,"venue_keys",tuple(self.venue_keys))
        if self.change_types!=tuple(sorted(set(self.change_types))):
            raise ValueError("change_types must be unique and sorted")
        if self.venue_keys!=tuple(sorted(set(self.venue_keys))):
            raise ValueError("venue_keys must be unique and sorted")
        if not self.canonical_market_id or not self.profile_hash:
            raise ValueError("state record identifiers must be non-empty")

    @property
    def record_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "profile_hash":self.profile_hash,
            "change_types":self.change_types,
            "venue_keys":self.venue_keys,
        })

@dataclass(frozen=True,slots=True)
class ConvergenceStateSnapshot:
    as_of:datetime
    registry_hash:str
    records:Tuple[ConvergenceStateRecord,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"as_of",_utc(self.as_of))
        object.__setattr__(self,"records",tuple(self.records))
        if self.records!=tuple(sorted(self.records,key=lambda r:(r.canonical_market_id,r.record_hash))):
            raise ValueError("records must be deterministically sorted")
        if len({r.canonical_market_id for r in self.records})!=len(self.records):
            raise ValueError("snapshot markets must be unique")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_171_BUILD_ID:
            raise ValueError("lineage must belong to UMD-171")
        if self.registry_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include convergence market registry hash")

    def record_for_market(self,market_id:str)->ConvergenceStateRecord|None:
        for record in self.records:
            if record.canonical_market_id==market_id:
                return record
        return None

    @property
    def snapshot_hash(self)->str:
        return deterministic_sha256({
            "as_of":self.as_of,
            "registry_hash":self.registry_hash,
            "record_hashes":tuple(r.record_hash for r in self.records),
            "lineage":self.lineage,
        })

class ConvergenceStateSnapshotBuilder:
    __slots__=()

    def build(
        self,
        registry:ConvergenceMarketRegistry,
        *,
        as_of:datetime,
        lineage:ImmutableLineage,
    )->ConvergenceStateSnapshot:
        if not isinstance(registry,ConvergenceMarketRegistry):
            raise TypeError("registry must be ConvergenceMarketRegistry")
        records=tuple(
            ConvergenceStateRecord(
                p.canonical_market_id,p.profile_hash,p.change_types,p.venue_keys
            )
            for p in registry.profiles
        )
        return ConvergenceStateSnapshot(as_of,registry.registry_hash,records,lineage)

def build_umd_171_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_171_BUILD_ID,"revision":UMD_171_REVISION,
        "schema_version":UMD_171_SCHEMA_VERSION,"upstream_builds":("UMD-170",),
        "mode":"deterministic_read_only_convergence_state_snapshot",
        "semantics":"enriched_point_in_time_convergence_state_only",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_171_convergence_state_snapshot()->bool:
    if verify_umd_170_convergence_market_registry() is not True:
        return False
    m=build_umd_171_certification_manifest()
    return m["build_id"]=="UMD-171" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
