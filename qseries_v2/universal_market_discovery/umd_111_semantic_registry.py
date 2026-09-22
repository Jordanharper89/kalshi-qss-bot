from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_109_market_semantic_profile import MarketSemanticProfile
from .umd_110_market_family_resolution import MarketFamily,verify_umd_110_market_family_resolution
UMD_111_BUILD_ID="UMD-111"; UMD_111_REVISION="UMD_111_SEMANTIC_REGISTRY_V1"; UMD_111_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
def _freeze_index(source): return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})
@dataclass(frozen=True,slots=True)
class SemanticRegistry:
    profiles:Tuple[MarketSemanticProfile,...]; families:Tuple[MarketFamily,...]; fact_index:Mapping[str,Tuple[str,...]]; family_index:Mapping[str,Tuple[str,...]]; lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"profiles",tuple(self.profiles)); object.__setattr__(self,"families",tuple(self.families))
        object.__setattr__(self,"fact_index",_freeze_index(self.fact_index)); object.__setattr__(self,"family_index",_freeze_index(self.family_index))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_111_BUILD_ID: raise ValueError("lineage must belong to UMD-111")
        required={p.profile_hash for p in self.profiles}|{f.family_hash for f in self.families}
        if not required.issubset(set(self.lineage.parent_hashes)): raise ValueError("lineage must include every profile and family hash")
    def markets_with(self,kind:str,key:str)->Tuple[str,...]: return self.fact_index.get(kind+"="+key,())
    def family_members(self,family_key:str)->Tuple[str,...]: return self.family_index.get(family_key,())
    @property
    def registry_hash(self):
        return deterministic_sha256({"profile_hashes":tuple(p.profile_hash for p in self.profiles),"family_hashes":tuple(f.family_hash for f in self.families),
            "fact_index":self.fact_index,"family_index":self.family_index,"lineage":self.lineage})
class SemanticRegistryBuilder:
    __slots__=()
    def build(self,profiles:Iterable[MarketSemanticProfile],families:Iterable[MarketFamily],*,lineage:ImmutableLineage)->SemanticRegistry:
        ps=tuple(sorted(profiles,key=lambda p:p.canonical_market_id)); fs=tuple(sorted(families,key=lambda f:f.family_key))
        if any(not isinstance(p,MarketSemanticProfile) for p in ps): raise TypeError("profiles must contain MarketSemanticProfile")
        if any(not isinstance(f,MarketFamily) for f in fs): raise TypeError("families must contain MarketFamily")
        fact={}
        for p in ps:
            for f in p.facts: fact.setdefault(f.kind+"="+f.key,[]).append(p.canonical_market_id)
        fam={f.family_key:list(f.member_market_ids) for f in fs}
        for d in (fact,fam):
            for k,v in d.items(): d[k]=tuple(sorted(set(v)))
        return SemanticRegistry(ps,fs,fact,fam,lineage)
def build_umd_111_certification_manifest():
    d={"subsystem_id":"UMD","build_id":UMD_111_BUILD_ID,"revision":UMD_111_REVISION,"schema_version":UMD_111_SCHEMA_VERSION,"upstream_builds":("UMD-109","UMD-110"),
       "mode":"deterministic_read_only_semantic_registry","prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})
def verify_umd_111_semantic_registry()->bool:
    if verify_umd_110_market_family_resolution() is not True:return False
    m=build_umd_111_certification_manifest()
    return m["build_id"]=="UMD-111" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
