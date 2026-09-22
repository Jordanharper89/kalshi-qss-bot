from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_103_canonical_market_registry import CanonicalMarketRegistry, verify_umd_103_canonical_market_registry

UMD_104_BUILD_ID="UMD-104"; UMD_104_REVISION="UMD_104_REGISTRY_SNAPSHOT_V1"; UMD_104_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class RegistrySnapshot:
    registry_hash:str
    record_ids:Tuple[str,...]
    record_hashes:Tuple[str,...]
    lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"record_ids",tuple(self.record_ids)); object.__setattr__(self,"record_hashes",tuple(self.record_hashes))
        if len(self.record_ids)!=len(self.record_hashes): raise ValueError("record_ids and record_hashes length mismatch")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_104_BUILD_ID: raise ValueError("lineage must belong to UMD-104")
        if self.registry_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include registry hash")
    def to_canonical_dict(self): return {"registry_hash":self.registry_hash,"record_ids":self.record_ids,"record_hashes":self.record_hashes,"lineage":self.lineage}
    @property
    def snapshot_hash(self): return deterministic_sha256(self.to_canonical_dict())

class RegistrySnapshotBuilder:
    __slots__=()
    def build(self,registry:CanonicalMarketRegistry,*,lineage:ImmutableLineage)->RegistrySnapshot:
        if not isinstance(registry,CanonicalMarketRegistry): raise TypeError("registry must be CanonicalMarketRegistry")
        return RegistrySnapshot(registry.registry_hash,tuple(r.canonical_market_id for r in registry.records),tuple(r.record_hash for r in registry.records),lineage)

def build_umd_104_certification_manifest():
    d={"subsystem_id":"UMD","build_id":UMD_104_BUILD_ID,"revision":UMD_104_REVISION,"schema_version":UMD_104_SCHEMA_VERSION,
       "upstream_builds":("UMD-103",),"mode":"deterministic_read_only_registry_snapshot","prohibited_capabilities":PROHIBITED_CAPABILITIES,
       "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})
def verify_umd_104_registry_snapshot()->bool:
    if verify_umd_103_canonical_market_registry() is not True:return False
    m=build_umd_104_certification_manifest()
    return m["build_id"]=="UMD-104" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
