from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_103_canonical_market_registry import CanonicalMarketRegistry
from .umd_106_registry_query_engine import verify_umd_106_registry_query_engine

UMD_107_BUILD_ID="UMD-107"
UMD_107_REVISION="UMD_107_REGISTRY_INDEX_BUILDER_V1"
UMD_107_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze_map(d):
    return MappingProxyType({k:tuple(v) for k,v in sorted(d.items())})

@dataclass(frozen=True,slots=True)
class RegistryIndexes:
    canonical_ids:Mapping[str,int]
    venue_index:Mapping[str,Tuple[str,...]]
    taxonomy_index:Mapping[str,Tuple[str,...]]
    alias_index:Mapping[str,Tuple[str,...]]
    relationship_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"canonical_ids",MappingProxyType(dict(sorted(self.canonical_ids.items()))))
        object.__setattr__(self,"venue_index",_freeze_map(self.venue_index))
        object.__setattr__(self,"taxonomy_index",_freeze_map(self.taxonomy_index))
        object.__setattr__(self,"alias_index",_freeze_map(self.alias_index))
        object.__setattr__(self,"relationship_index",_freeze_map(self.relationship_index))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_107_BUILD_ID:
            raise ValueError("lineage must belong to UMD-107")
    @property
    def index_hash(self):
        return deterministic_sha256({
            "canonical_ids":self.canonical_ids,
            "venue_index":self.venue_index,
            "taxonomy_index":self.taxonomy_index,
            "alias_index":self.alias_index,
            "relationship_index":self.relationship_index,
            "lineage":self.lineage,
        })

class RegistryIndexBuilder:
    __slots__=()
    def build(self,registry:CanonicalMarketRegistry,*,lineage:ImmutableLineage)->RegistryIndexes:
        if not isinstance(registry,CanonicalMarketRegistry): raise TypeError("registry must be CanonicalMarketRegistry")
        canonical={}; venue={}; taxonomy={}; alias={}; relationship={}
        for pos,record in enumerate(registry.records):
            cid=record.canonical_market_id
            canonical[cid]=pos
            taxonomy.setdefault(record.taxonomy_key,[]).append(cid)
            for binding in record.venue_bindings:
                venue.setdefault(binding.venue_key,[]).append(cid)
            for key in record.alias_keys:
                alias.setdefault(key,[]).append(cid)
            for rh in record.relationship_hashes:
                relationship.setdefault(rh,[]).append(cid)
        for bucket in (venue,taxonomy,alias,relationship):
            for k,v in bucket.items(): bucket[k]=tuple(sorted(set(v)))
        return RegistryIndexes(canonical,venue,taxonomy,alias,relationship,lineage)

def build_umd_107_certification_manifest():
    d={"subsystem_id":"UMD","build_id":UMD_107_BUILD_ID,"revision":UMD_107_REVISION,"schema_version":UMD_107_SCHEMA_VERSION,
       "upstream_builds":("UMD-103","UMD-106"),"mode":"deterministic_read_only_registry_indexing",
       "prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,
       "mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})

def verify_umd_107_registry_index_builder()->bool:
    if verify_umd_106_registry_query_engine() is not True:return False
    m=build_umd_107_certification_manifest()
    return m["build_id"]=="UMD-107" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
