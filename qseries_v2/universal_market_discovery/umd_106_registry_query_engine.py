from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_103_canonical_market_registry import CanonicalMarketRegistry, CanonicalMarketRecord
from .umd_105_registry_diff import verify_umd_105_registry_diff

UMD_106_BUILD_ID="UMD-106"
UMD_106_REVISION="UMD_106_REGISTRY_QUERY_ENGINE_V1"
UMD_106_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class RegistryQueryResult:
    query_type:str
    query_key:str
    records:Tuple[CanonicalMarketRecord,...]
    lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"records",tuple(self.records))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_106_BUILD_ID:
            raise ValueError("lineage must belong to UMD-106")
    @property
    def result_hash(self):
        return deterministic_sha256({
            "query_type":self.query_type,
            "query_key":self.query_key,
            "record_hashes":tuple(r.record_hash for r in self.records),
            "lineage":self.lineage,
        })

class RegistryQueryEngine:
    __slots__=("registry",)
    def __init__(self,registry:CanonicalMarketRegistry):
        if not isinstance(registry,CanonicalMarketRegistry):
            raise TypeError("registry must be CanonicalMarketRegistry")
        self.registry=registry

    def by_canonical_id(self,canonical_market_id:str,*,lineage:ImmutableLineage)->RegistryQueryResult:
        record=self.registry.get(canonical_market_id)
        records=() if record is None else (record,)
        return RegistryQueryResult("canonical_id",canonical_market_id,records,lineage)

    def by_venue_market(self,venue:str,venue_market_id:str,*,lineage:ImmutableLineage)->RegistryQueryResult:
        matches=[]
        for record in self.registry.records:
            for binding in record.venue_bindings:
                if binding.venue_key==venue and binding.venue_market_id==venue_market_id:
                    matches.append(record); break
        matches=tuple(sorted(matches,key=lambda r:r.canonical_market_id))
        return RegistryQueryResult("venue_market",f"{venue}:{venue_market_id}",matches,lineage)

    def by_taxonomy(self,taxonomy_key:str,*,lineage:ImmutableLineage)->RegistryQueryResult:
        matches=tuple(r for r in self.registry.records if r.taxonomy_key==taxonomy_key)
        return RegistryQueryResult("taxonomy",taxonomy_key,matches,lineage)

def build_umd_106_certification_manifest():
    d={"subsystem_id":"UMD","build_id":UMD_106_BUILD_ID,"revision":UMD_106_REVISION,"schema_version":UMD_106_SCHEMA_VERSION,
       "upstream_builds":("UMD-103","UMD-105"),"mode":"deterministic_read_only_registry_query",
       "prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,
       "mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})

def verify_umd_106_registry_query_engine()->bool:
    if verify_umd_105_registry_diff() is not True:return False
    m=build_umd_106_certification_manifest()
    return m["build_id"]=="UMD-106" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
