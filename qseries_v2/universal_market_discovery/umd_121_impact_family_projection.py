from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_110_market_family_resolution import MarketFamily
from .umd_119_impact_provenance import ImpactProvenanceBundle
from .umd_120_impact_query_engine import verify_umd_120_impact_query_engine

UMD_121_BUILD_ID="UMD-121"
UMD_121_REVISION="UMD_121_IMPACT_FAMILY_PROJECTION_V1"
UMD_121_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class FamilyImpact:
    family_key:str
    family_hash:str
    impacted_market_ids:Tuple[str,...]
    direct_market_ids:Tuple[str,...]
    propagated_market_ids:Tuple[str,...]

    def __post_init__(self):
        for name in ("impacted_market_ids","direct_market_ids","propagated_market_ids"):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        if set(self.direct_market_ids)|set(self.propagated_market_ids) != set(self.impacted_market_ids):
            raise ValueError("direct and propagated markets must exactly cover impacted markets")
        if set(self.direct_market_ids)&set(self.propagated_market_ids):
            raise ValueError("market cannot be both direct and propagated within one projection")

    @property
    def impact_hash(self)->str:
        return deterministic_sha256({
            "family_key":self.family_key,
            "family_hash":self.family_hash,
            "impacted_market_ids":self.impacted_market_ids,
            "direct_market_ids":self.direct_market_ids,
            "propagated_market_ids":self.propagated_market_ids,
        })

@dataclass(frozen=True,slots=True)
class FamilyImpactProjection:
    observation_hash:str
    family_impacts:Tuple[FamilyImpact,...]
    unmatched_market_ids:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"family_impacts",tuple(self.family_impacts))
        object.__setattr__(self,"unmatched_market_ids",tuple(self.unmatched_market_ids))
        if tuple(sorted(self.family_impacts,key=lambda x:(x.family_key,x.family_hash)))!=self.family_impacts:
            raise ValueError("family_impacts must be deterministically sorted")
        if self.unmatched_market_ids!=tuple(sorted(set(self.unmatched_market_ids))):
            raise ValueError("unmatched_market_ids must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_121_BUILD_ID:
            raise ValueError("lineage must belong to UMD-121")

    def markets_in_family(self,family_key:str)->Tuple[str,...]:
        for impact in self.family_impacts:
            if impact.family_key==family_key:
                return impact.impacted_market_ids
        return ()

    @property
    def projection_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "family_impact_hashes":tuple(x.impact_hash for x in self.family_impacts),
            "unmatched_market_ids":self.unmatched_market_ids,
            "lineage":self.lineage,
        })

class ImpactFamilyProjector:
    __slots__=()

    def project(
        self,
        bundle:ImpactProvenanceBundle,
        families:Iterable[MarketFamily],
        *,
        lineage:ImmutableLineage,
    )->FamilyImpactProjection:
        if not isinstance(bundle,ImpactProvenanceBundle):
            raise TypeError("bundle must be ImpactProvenanceBundle")
        fs=tuple(families)
        if any(not isinstance(f,MarketFamily) for f in fs):
            raise TypeError("families must contain MarketFamily")

        entries={e.canonical_market_id:e for e in bundle.entries}
        impacted=set(entries)
        assigned=set()
        results=[]

        for family in sorted(fs,key=lambda f:(f.family_key,f.family_hash)):
            members=tuple(sorted(impacted & set(family.member_market_ids)))
            if not members:
                continue
            direct=tuple(m for m in members if entries[m].direct)
            propagated=tuple(m for m in members if not entries[m].direct)
            results.append(FamilyImpact(
                family.family_key,
                family.family_hash,
                members,
                direct,
                propagated,
            ))
            assigned.update(members)

        return FamilyImpactProjection(
            bundle.observation_hash,
            tuple(results),
            tuple(sorted(impacted-assigned)),
            lineage,
        )

def build_umd_121_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_121_BUILD_ID,"revision":UMD_121_REVISION,
        "schema_version":UMD_121_SCHEMA_VERSION,"upstream_builds":("UMD-110","UMD-119","UMD-120"),
        "mode":"deterministic_read_only_impact_family_projection",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_121_impact_family_projection()->bool:
    if verify_umd_120_impact_query_engine() is not True:
        return False
    m=build_umd_121_certification_manifest()
    return m["build_id"]=="UMD-121" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
