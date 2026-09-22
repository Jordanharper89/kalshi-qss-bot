from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_119_impact_provenance import ImpactProvenanceBundle,MarketImpactProvenance,verify_umd_119_impact_provenance_bundle

UMD_120_BUILD_ID="UMD-120"
UMD_120_REVISION="UMD_120_IMPACT_QUERY_ENGINE_V1"
UMD_120_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ImpactQueryResult:
    query_type:str
    query_key:str
    entries:Tuple[MarketImpactProvenance,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"entries",tuple(self.entries))
        if tuple(sorted(self.entries,key=lambda e:(e.canonical_market_id,e.provenance_hash)))!=self.entries:
            raise ValueError("entries must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_120_BUILD_ID:
            raise ValueError("lineage must belong to UMD-120")

    @property
    def result_hash(self)->str:
        return deterministic_sha256({
            "query_type":self.query_type,
            "query_key":self.query_key,
            "provenance_hashes":tuple(e.provenance_hash for e in self.entries),
            "lineage":self.lineage,
        })

class ImpactQueryEngine:
    __slots__=("bundles",)

    def __init__(self,bundles:Iterable[ImpactProvenanceBundle]):
        values=tuple(bundles)
        if any(not isinstance(b,ImpactProvenanceBundle) for b in values):
            raise TypeError("bundles must contain ImpactProvenanceBundle")
        self.bundles=tuple(sorted(values,key=lambda b:(b.observation_hash,b.bundle_hash)))

    def by_observation(self,observation_hash:str,*,lineage:ImmutableLineage)->ImpactQueryResult:
        entries=[]
        for b in self.bundles:
            if b.observation_hash==observation_hash:
                entries.extend(b.entries)
        return self._result("observation",observation_hash,entries,lineage)

    def by_market(self,canonical_market_id:str,*,lineage:ImmutableLineage)->ImpactQueryResult:
        entries=[]
        for b in self.bundles:
            entry=b.for_market(canonical_market_id)
            if entry is not None:
                entries.append(entry)
        return self._result("market",canonical_market_id,entries,lineage)

    def by_dependency(self,kind:str,key:str,*,lineage:ImmutableLineage)->ImpactQueryResult:
        entries=[]
        for b in self.bundles:
            for entry in b.entries:
                if (kind,key) in entry.dependency_matches:
                    entries.append(entry)
        return self._result("dependency",kind+"="+key,entries,lineage)

    def by_impact_type(self,direct:bool,*,lineage:ImmutableLineage)->ImpactQueryResult:
        entries=[]
        for b in self.bundles:
            entries.extend(e for e in b.entries if e.direct is direct)
        return self._result("impact_type","direct" if direct else "propagated",entries,lineage)

    @staticmethod
    def _result(query_type,query_key,entries,lineage):
        values=tuple(sorted(entries,key=lambda e:(e.canonical_market_id,e.provenance_hash)))
        return ImpactQueryResult(query_type,query_key,values,lineage)

def build_umd_120_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_120_BUILD_ID,"revision":UMD_120_REVISION,
        "schema_version":UMD_120_SCHEMA_VERSION,"upstream_builds":("UMD-119",),
        "mode":"deterministic_read_only_impact_query_engine",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_120_impact_query_engine()->bool:
    if verify_umd_119_impact_provenance_bundle() is not True:
        return False
    m=build_umd_120_certification_manifest()
    return m["build_id"]=="UMD-120" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
