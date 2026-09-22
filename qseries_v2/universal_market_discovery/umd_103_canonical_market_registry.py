from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Any, Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_102_canonical_market_record import CanonicalMarketRecord, verify_umd_102_canonical_market_record_assembly

UMD_103_BUILD_ID="UMD-103"
UMD_103_REVISION="UMD_103_CANONICAL_MARKET_REGISTRY_V1"
UMD_103_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class CanonicalMarketRegistry:
    records:Tuple[CanonicalMarketRecord,...]
    lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"records",tuple(self.records))
        ids=[r.canonical_market_id for r in self.records]
        if len(ids)!=len(set(ids)): raise ValueError("duplicate canonical_market_id in registry")
        if tuple(ids)!=tuple(sorted(ids)): raise ValueError("records must be sorted by canonical_market_id")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_103_BUILD_ID:
            raise ValueError("lineage must belong to UMD-103")
        required={r.record_hash for r in self.records}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every record hash")
    def get(self,canonical_market_id:str)->CanonicalMarketRecord|None:
        for r in self.records:
            if r.canonical_market_id==canonical_market_id:return r
        return None
    def to_canonical_dict(self):
        return {"record_hashes":tuple(r.record_hash for r in self.records),"lineage":self.lineage}
    @property
    def registry_hash(self): return deterministic_sha256(self.to_canonical_dict())

class CanonicalMarketRegistryBuilder:
    __slots__=()
    def build(self,records:Iterable[CanonicalMarketRecord],*,lineage:ImmutableLineage)->CanonicalMarketRegistry:
        vals=tuple(records)
        if any(not isinstance(x,CanonicalMarketRecord) for x in vals): raise TypeError("records must contain CanonicalMarketRecord")
        vals=tuple(sorted(vals,key=lambda r:r.canonical_market_id))
        return CanonicalMarketRegistry(vals,lineage)

def build_umd_103_certification_manifest():
    d={"subsystem_id":"UMD","build_id":UMD_103_BUILD_ID,"revision":UMD_103_REVISION,"schema_version":UMD_103_SCHEMA_VERSION,
       "upstream_builds":("UMD-102",),"mode":"deterministic_read_only_canonical_registry","prohibited_capabilities":PROHIBITED_CAPABILITIES,
       "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})
def verify_umd_103_canonical_market_registry()->bool:
    if verify_umd_102_canonical_market_record_assembly() is not True:return False
    m=build_umd_103_certification_manifest()
    return m["build_id"]=="UMD-103" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
