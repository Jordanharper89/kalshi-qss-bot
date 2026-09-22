from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_103_canonical_market_registry import CanonicalMarketRegistry, CanonicalMarketRecord
from .umd_107_registry_index_builder import RegistryIndexes, verify_umd_107_registry_index_builder

UMD_108_BUILD_ID="UMD-108"
UMD_108_REVISION="UMD_108_REGISTRY_SEARCH_ENGINE_V1"
UMD_108_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _norm(value:str)->str:
    return " ".join(str(value).strip().casefold().split())

def _alias_key(value:str)->str:
    import re, unicodedata
    value=unicodedata.normalize("NFKC",str(value))
    value=" ".join(value.strip().casefold().split())
    return re.sub(r"[^a-z0-9]+","-",value).strip("-")

@dataclass(frozen=True,slots=True)
class RegistrySearchHit:
    canonical_market_id:str
    score:int
    reasons:Tuple[str,...]
    record_hash:str

@dataclass(frozen=True,slots=True)
class RegistrySearchResult:
    query:str
    hits:Tuple[RegistrySearchHit,...]
    lineage:ImmutableLineage
    def __post_init__(self):
        object.__setattr__(self,"hits",tuple(self.hits))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_108_BUILD_ID:
            raise ValueError("lineage must belong to UMD-108")
    @property
    def result_hash(self):
        return deterministic_sha256({
            "query": self.query,
            "hits": tuple(
                {
                    "canonical_market_id": hit.canonical_market_id,
                    "score": hit.score,
                    "reasons": tuple(hit.reasons),
                    "record_hash": hit.record_hash,
                }
                for hit in self.hits
            ),
            "lineage": self.lineage,
        })

class RegistrySearchEngine:
    __slots__=("registry","indexes")
    def __init__(self,registry:CanonicalMarketRegistry,indexes:RegistryIndexes):
        if not isinstance(registry,CanonicalMarketRegistry): raise TypeError("registry must be CanonicalMarketRegistry")
        if not isinstance(indexes,RegistryIndexes): raise TypeError("indexes must be RegistryIndexes")
        self.registry=registry; self.indexes=indexes

    def search(self,query:str,*,taxonomy_key:str|None=None,lineage:ImmutableLineage)->RegistrySearchResult:
        q=_norm(query)
        hits=[]
        for record in self.registry.records:
            if taxonomy_key is not None and record.taxonomy_key!=taxonomy_key:
                continue
            score=0; reasons=[]
            cid=_norm(record.canonical_market_id)
            if q and q==cid: score+=100; reasons.append("canonical_exact")
            elif q and cid.startswith(q): score+=60; reasons.append("canonical_prefix")
            aq=_alias_key(query)
            if aq and aq in record.alias_keys:
                score+=90; reasons.append("alias_exact")
            if aq and any(a.startswith(aq) for a in record.alias_keys):
                score+=40; reasons.append("alias_prefix")
            if taxonomy_key is not None:
                score+=10; reasons.append("taxonomy_filter")
            if score:
                hits.append(RegistrySearchHit(record.canonical_market_id,score,tuple(sorted(set(reasons))),record.record_hash))
        hits.sort(key=lambda h:(-h.score,h.canonical_market_id,h.record_hash))
        return RegistrySearchResult(query,tuple(hits),lineage)

def build_umd_108_certification_manifest():
    d={"subsystem_id":"UMD","build_id":UMD_108_BUILD_ID,"revision":UMD_108_REVISION,"schema_version":UMD_108_SCHEMA_VERSION,
       "upstream_builds":("UMD-103","UMD-107"),"mode":"deterministic_read_only_registry_search",
       "prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,
       "mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})

def verify_umd_108_registry_search_engine()->bool:
    if verify_umd_107_registry_index_builder() is not True:return False
    m=build_umd_108_certification_manifest()
    return m["build_id"]=="UMD-108" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
