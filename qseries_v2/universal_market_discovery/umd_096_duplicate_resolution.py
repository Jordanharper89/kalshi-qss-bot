from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any,Iterable,Mapping,Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_095_market_identity import CanonicalMarketIdentity,verify_umd_095_canonical_market_identity_resolution
UMD_096_BUILD_ID="UMD-096"
UMD_096_BUILD_NAME="Cross-Venue Duplicate Resolution"
UMD_096_REVISION="UMD_096_CROSS_VENUE_DUPLICATE_RESOLUTION_V1"
UMD_096_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
def _freeze(v):
    if v is None:v={}
    if not isinstance(v,Mapping):raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k),x) for k,x in v.items())))
@dataclass(frozen=True,slots=True)
class DuplicateGroup:
    canonical_market_id:str
    identity_key:str
    member_identity_hashes:Tuple[str,...]
    venue_keys:Tuple[str,...]
    venue_market_ids:Tuple[str,...]
    primary_identity_hash:str
    metadata:Mapping[str,Any]
    lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"member_identity_hashes",tuple(self.member_identity_hashes)); object.__setattr__(self,"venue_keys",tuple(self.venue_keys)); object.__setattr__(self,"venue_market_ids",tuple(self.venue_market_ids)); object.__setattr__(self,"metadata",_freeze(self.metadata))
        n=len(self.member_identity_hashes)
        if n<2: raise ValueError("duplicate group requires at least two members")
        if len(self.venue_keys)!=n or len(self.venue_market_ids)!=n: raise ValueError("member collections must align")
        if len(set(self.member_identity_hashes))!=n: raise ValueError("member identities must be unique")
        if len(set(self.venue_keys))<2: raise ValueError("duplicate group must span at least two venues")
        if self.primary_identity_hash!=min(self.member_identity_hashes): raise ValueError("primary identity must be deterministic minimum hash")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_096_BUILD_ID: raise ValueError("lineage must belong to UMD-096")
        if not set(self.member_identity_hashes).issubset(set(self.lineage.parent_hashes)): raise ValueError("lineage must include every member identity hash")
    def to_canonical_dict(self):return {"canonical_market_id":self.canonical_market_id,"identity_key":self.identity_key,"member_identity_hashes":self.member_identity_hashes,"venue_keys":self.venue_keys,"venue_market_ids":self.venue_market_ids,"primary_identity_hash":self.primary_identity_hash,"metadata":self.metadata,"lineage":self.lineage}
    @property
    def group_hash(self):return deterministic_sha256(self.to_canonical_dict())
class CrossVenueDuplicateResolver:
    __slots__=()
    def resolve(self,identities:Iterable[CanonicalMarketIdentity],*,lineage:ImmutableLineage,metadata:Mapping[str,Any]|None=None)->Tuple[DuplicateGroup,...]:
        values=tuple(identities)
        if any(not isinstance(x,CanonicalMarketIdentity) for x in values):raise TypeError("all identities must be CanonicalMarketIdentity")
        buckets={}
        for item in values:buckets.setdefault(item.identity_key,[]).append(item)
        groups=[]
        for key in sorted(buckets):
            members=buckets[key]
            if len({m.venue_key for m in members})<2:continue
            ordered=sorted(members,key=lambda m:(m.identity_hash,m.venue_key,m.venue_market_id))
            groups.append(DuplicateGroup(canonical_market_id=ordered[0].canonical_market_id,identity_key=key,member_identity_hashes=tuple(m.identity_hash for m in ordered),venue_keys=tuple(m.venue_key for m in ordered),venue_market_ids=tuple(m.venue_market_id for m in ordered),primary_identity_hash=min(m.identity_hash for m in ordered),metadata={} if metadata is None else metadata,lineage=lineage))
        return tuple(groups)
def build_umd_096_certification_manifest():
    data={"subsystem_id":"UMD","build_id":UMD_096_BUILD_ID,"revision":UMD_096_REVISION,"schema_version":UMD_096_SCHEMA_VERSION,"upstream_builds":("UMD-093","UMD-094","UMD-095"),"mode":"deterministic_read_only_cross_venue_duplicate_resolution","prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})
def verify_umd_096_cross_venue_duplicate_resolution()->bool:
    if verify_umd_095_canonical_market_identity_resolution() is not True:return False
    m=build_umd_096_certification_manifest();return m["build_id"]=="UMD-096" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
