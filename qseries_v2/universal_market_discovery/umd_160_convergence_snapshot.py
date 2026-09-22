from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime,timezone
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_159_change_convergence_registry import ChangeConvergenceRegistry,verify_umd_159_change_convergence_registry

UMD_160_BUILD_ID="UMD-160"
UMD_160_REVISION="UMD_160_CONVERGENCE_SNAPSHOT_V1"
UMD_160_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _utc(value:datetime)->datetime:
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True,slots=True)
class ConvergenceSnapshotRecord:
    canonical_market_id:str
    convergence_hashes:Tuple[str,...]
    change_hashes:Tuple[str,...]

    def __post_init__(self):
        object.__setattr__(self,"convergence_hashes",tuple(self.convergence_hashes))
        object.__setattr__(self,"change_hashes",tuple(self.change_hashes))
        if not self.canonical_market_id:
            raise ValueError("canonical_market_id must be non-empty")
        if self.convergence_hashes!=tuple(sorted(set(self.convergence_hashes))):
            raise ValueError("convergence_hashes must be unique and sorted")
        if self.change_hashes!=tuple(sorted(set(self.change_hashes))):
            raise ValueError("change_hashes must be unique and sorted")
        if not self.convergence_hashes:
            raise ValueError("snapshot record requires convergence")
        if len(self.change_hashes)<2:
            raise ValueError("snapshot convergence requires at least two distinct changes")

    @property
    def record_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "convergence_hashes":self.convergence_hashes,
            "change_hashes":self.change_hashes,
        })

@dataclass(frozen=True,slots=True)
class ConvergenceSnapshot:
    as_of:datetime
    registry_hash:str
    records:Tuple[ConvergenceSnapshotRecord,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"as_of",_utc(self.as_of))
        object.__setattr__(self,"records",tuple(self.records))
        if self.records!=tuple(sorted(self.records,key=lambda r:(r.canonical_market_id,r.record_hash))):
            raise ValueError("records must be deterministically sorted")
        if len({r.canonical_market_id for r in self.records})!=len(self.records):
            raise ValueError("snapshot markets must be unique")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_160_BUILD_ID:
            raise ValueError("lineage must belong to UMD-160")
        if self.registry_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include convergence registry hash")

    def record_for_market(self,market_id:str)->ConvergenceSnapshotRecord|None:
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

class ConvergenceSnapshotBuilder:
    __slots__=()

    def build(
        self,
        registry:ChangeConvergenceRegistry,
        *,
        as_of:datetime,
        lineage:ImmutableLineage,
    )->ConvergenceSnapshot:
        if not isinstance(registry,ChangeConvergenceRegistry):
            raise TypeError("registry must be ChangeConvergenceRegistry")

        changes_by_market={}
        for change_hash,markets in registry.change_index.items():
            for market_id in markets:
                changes_by_market.setdefault(market_id,[]).append(change_hash)

        records=[]
        for market_id,convergence_hashes in sorted(registry.market_index.items()):
            changes=tuple(sorted(set(changes_by_market.get(market_id,()))))
            if len(changes)<2:
                raise ValueError("convergence registry market lacks two distinct changes")
            records.append(ConvergenceSnapshotRecord(
                market_id,
                tuple(sorted(set(convergence_hashes))),
                changes,
            ))

        return ConvergenceSnapshot(
            as_of,
            registry.registry_hash,
            tuple(records),
            lineage,
        )

def build_umd_160_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_160_BUILD_ID,"revision":UMD_160_REVISION,
        "schema_version":UMD_160_SCHEMA_VERSION,"upstream_builds":("UMD-159",),
        "mode":"deterministic_read_only_convergence_snapshot",
        "semantics":"point_in_time_structural_convergence_only",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_160_convergence_snapshot()->bool:
    if verify_umd_159_change_convergence_registry() is not True:
        return False
    m=build_umd_160_certification_manifest()
    return m["build_id"]=="UMD-160" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
