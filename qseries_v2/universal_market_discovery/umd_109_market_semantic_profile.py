from __future__ import annotations
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_102_canonical_market_record import CanonicalMarketRecord
from .umd_108_registry_search_engine import verify_umd_108_registry_search_engine
UMD_109_BUILD_ID="UMD-109"; UMD_109_REVISION="UMD_109_MARKET_SEMANTIC_PROFILE_V1"; UMD_109_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
SEMANTIC_KINDS=("entity","asset","event","metric","operator","threshold","unit","geography","time_window","settlement_source","market_type")
_KEY_RE=re.compile(r"[^a-z0-9]+")
def semantic_key(value:str)->str:
    if not isinstance(value,str): raise TypeError("semantic value must be a string")
    value=_KEY_RE.sub("-",value.strip().casefold()).strip("-")
    if not value: raise ValueError("semantic value must contain letters or digits")
    return value
@dataclass(frozen=True,slots=True)
class SemanticFact:
    kind:str; value:str; key:str
    def __post_init__(self):
        if self.kind not in SEMANTIC_KINDS: raise ValueError("unsupported semantic fact kind")
        if self.key!=semantic_key(self.value): raise ValueError("semantic fact key does not match value")
    @property
    def fact_hash(self): return deterministic_sha256({"kind":self.kind,"key":self.key})
@dataclass(frozen=True,slots=True)
class MarketSemanticProfile:
    canonical_market_id:str; record_hash:str; facts:Tuple[SemanticFact,...]; lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"facts",tuple(self.facts))
        if tuple(sorted(self.facts,key=lambda f:(f.kind,f.key)))!=self.facts: raise ValueError("facts must be deterministically sorted")
        pairs=[(f.kind,f.key) for f in self.facts]
        if len(pairs)!=len(set(pairs)): raise ValueError("duplicate semantic facts")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_109_BUILD_ID: raise ValueError("lineage must belong to UMD-109")
        if self.record_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include canonical record hash")
    def values(self,kind:str)->Tuple[str,...]: return tuple(f.key for f in self.facts if f.kind==kind)
    @property
    def profile_hash(self):
        return deterministic_sha256({"canonical_market_id":self.canonical_market_id,"record_hash":self.record_hash,
            "facts":tuple({"kind":f.kind,"key":f.key} for f in self.facts),"lineage":self.lineage})
class MarketSemanticProfiler:
    __slots__=()
    def build(self,record:CanonicalMarketRecord,facts:Iterable[tuple[str,str]],*,lineage:ImmutableLineage)->MarketSemanticProfile:
        if not isinstance(record,CanonicalMarketRecord): raise TypeError("record must be CanonicalMarketRecord")
        built=[]; seen=set()
        for kind,value in facts:
            key=semantic_key(value); pair=(kind,key)
            if pair in seen: continue
            seen.add(pair); built.append(SemanticFact(kind,value,key))
        built.sort(key=lambda f:(f.kind,f.key))
        return MarketSemanticProfile(record.canonical_market_id,record.record_hash,tuple(built),lineage)
def build_umd_109_certification_manifest():
    d={"subsystem_id":"UMD","build_id":UMD_109_BUILD_ID,"revision":UMD_109_REVISION,"schema_version":UMD_109_SCHEMA_VERSION,
       "upstream_builds":("UMD-102","UMD-108"),"mode":"deterministic_read_only_market_semantics","semantic_kinds":SEMANTIC_KINDS,
       "prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})
def verify_umd_109_market_semantic_profile()->bool:
    if verify_umd_108_registry_search_engine() is not True:return False
    m=build_umd_109_certification_manifest()
    return m["build_id"]=="UMD-109" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
