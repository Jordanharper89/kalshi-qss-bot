from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_109_market_semantic_profile import MarketSemanticProfile,verify_umd_109_market_semantic_profile
UMD_110_BUILD_ID="UMD-110"; UMD_110_REVISION="UMD_110_MARKET_FAMILY_RESOLUTION_V1"; UMD_110_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
DEFAULT_FAMILY_DIMENSIONS=("asset","event","metric","market_type")
@dataclass(frozen=True,slots=True)
class MarketFamily:
    family_key:str; dimensions:Tuple[str,...]; member_market_ids:Tuple[str,...]; member_profile_hashes:Tuple[str,...]; lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"dimensions",tuple(self.dimensions)); object.__setattr__(self,"member_market_ids",tuple(self.member_market_ids)); object.__setattr__(self,"member_profile_hashes",tuple(self.member_profile_hashes))
        if not self.member_market_ids: raise ValueError("market family requires at least one member")
        if len(self.member_market_ids)!=len(self.member_profile_hashes): raise ValueError("member ids and profile hashes length mismatch")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_110_BUILD_ID: raise ValueError("lineage must belong to UMD-110")
        if not set(self.member_profile_hashes).issubset(set(self.lineage.parent_hashes)): raise ValueError("lineage must include every member profile hash")
    @property
    def family_hash(self):
        return deterministic_sha256({"family_key":self.family_key,"dimensions":self.dimensions,"member_market_ids":self.member_market_ids,"member_profile_hashes":self.member_profile_hashes,"lineage":self.lineage})
class MarketFamilyResolver:
    __slots__=("dimensions",)
    def __init__(self,dimensions:Iterable[str]=DEFAULT_FAMILY_DIMENSIONS):
        dims=tuple(dimensions)
        if not dims or len(set(dims))!=len(dims): raise ValueError("dimensions must be non-empty and unique")
        self.dimensions=dims
    def family_key(self,profile:MarketSemanticProfile)->str:
        if not isinstance(profile,MarketSemanticProfile): raise TypeError("profile must be MarketSemanticProfile")
        return "|".join(dim+"="+(",".join(profile.values(dim)) if profile.values(dim) else "*") for dim in self.dimensions)
    def resolve(self,profiles:Iterable[MarketSemanticProfile],*,lineage_factory)->Tuple[MarketFamily,...]:
        vals=tuple(profiles)
        if any(not isinstance(p,MarketSemanticProfile) for p in vals): raise TypeError("profiles must contain MarketSemanticProfile")
        buckets={}
        for p in vals: buckets.setdefault(self.family_key(p),[]).append(p)
        out=[]
        for key,members in sorted(buckets.items()):
            members=tuple(sorted(members,key=lambda p:p.canonical_market_id))
            lineage=lineage_factory(tuple(p.profile_hash for p in members))
            out.append(MarketFamily(key,self.dimensions,tuple(p.canonical_market_id for p in members),tuple(p.profile_hash for p in members),lineage))
        return tuple(out)
def build_umd_110_certification_manifest():
    d={"subsystem_id":"UMD","build_id":UMD_110_BUILD_ID,"revision":UMD_110_REVISION,"schema_version":UMD_110_SCHEMA_VERSION,"upstream_builds":("UMD-109",),
       "mode":"deterministic_read_only_market_family_resolution","default_family_dimensions":DEFAULT_FAMILY_DIMENSIONS,"prohibited_capabilities":PROHIBITED_CAPABILITIES,
       "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})
def verify_umd_110_market_family_resolution()->bool:
    if verify_umd_109_market_semantic_profile() is not True:return False
    m=build_umd_110_certification_manifest()
    return m["build_id"]=="UMD-110" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
