from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_094_market_normalization import NormalizedMarket, verify_umd_094_market_normalization_foundation

UMD_095_BUILD_ID="UMD-095"
UMD_095_BUILD_NAME="Canonical Market Identity Resolution"
UMD_095_REVISION="UMD_095_CANONICAL_MARKET_IDENTITY_RESOLUTION_V1"
UMD_095_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")


def _freeze(v: Mapping[str,Any]|None)->Mapping[str,Any]:
    if v is None: v={}
    if not isinstance(v,Mapping): raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k),x) for k,x in v.items())))


def canonical_identity_key(market: NormalizedMarket) -> str:
    if not isinstance(market, NormalizedMarket): raise TypeError("market must be NormalizedMarket")
    payload={"title_key":market.title_key,"category_key":market.category_key,"close_time":market.close_time,"settlement_time":market.settlement_time,"outcome_keys":tuple(sorted(market.outcome_keys))}
    return deterministic_sha256(payload)

@dataclass(frozen=True,slots=True)
class CanonicalMarketIdentity:
    canonical_market_id:str
    identity_key:str
    source_market_hash:str
    venue_key:str
    venue_market_id:str
    title_key:str
    category_key:str
    close_time:str
    settlement_time:str
    outcome_keys:Tuple[str,...]
    metadata:Mapping[str,Any]
    lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"metadata",_freeze(self.metadata))
        expected="umd:market:"+self.identity_key
        if self.canonical_market_id!=expected: raise ValueError("canonical_market_id does not match identity_key")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_095_BUILD_ID: raise ValueError("lineage must belong to UMD-095")
        if self.source_market_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include source market hash")
    def to_canonical_dict(self):
        return {"canonical_market_id":self.canonical_market_id,"identity_key":self.identity_key,"source_market_hash":self.source_market_hash,"venue_key":self.venue_key,"venue_market_id":self.venue_market_id,"title_key":self.title_key,"category_key":self.category_key,"close_time":self.close_time,"settlement_time":self.settlement_time,"outcome_keys":self.outcome_keys,"metadata":self.metadata,"lineage":self.lineage}
    @property
    def identity_hash(self): return deterministic_sha256(self.to_canonical_dict())

class CanonicalMarketIdentityResolver:
    __slots__=()
    def resolve(self, market:NormalizedMarket, *, lineage:ImmutableLineage, metadata:Mapping[str,Any]|None=None)->CanonicalMarketIdentity:
        key=canonical_identity_key(market)
        return CanonicalMarketIdentity(canonical_market_id="umd:market:"+key,identity_key=key,source_market_hash=market.normalized_market_hash,venue_key=market.venue_key,venue_market_id=market.venue_market_id,title_key=market.title_key,category_key=market.category_key,close_time=market.close_time,settlement_time=market.settlement_time,outcome_keys=tuple(sorted(market.outcome_keys)),metadata={} if metadata is None else metadata,lineage=lineage)

def build_umd_095_certification_manifest():
    data={"subsystem_id":"UMD","build_id":UMD_095_BUILD_ID,"revision":UMD_095_REVISION,"schema_version":UMD_095_SCHEMA_VERSION,"upstream_builds":("UMD-093","UMD-094"),"mode":"deterministic_read_only_identity_resolution","prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_095_canonical_market_identity_resolution()->bool:
    if verify_umd_094_market_normalization_foundation() is not True: return False
    m=build_umd_095_certification_manifest(); return m["build_id"]=="UMD-095" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
