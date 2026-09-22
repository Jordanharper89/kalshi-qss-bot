from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_121_impact_family_projection import FamilyImpactProjection
from .umd_124_cross_venue_cohort import CrossVenueImpactCohort, verify_umd_124_cross_venue_impact_cohort

UMD_125_BUILD_ID="UMD-125"
UMD_125_REVISION="UMD_125_IMPACT_COVERAGE_MATRIX_V1"
UMD_125_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze_index(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ImpactCoverageMatrix:
    observation_hash:str
    family_to_markets:Mapping[str,Tuple[str,...]]
    venue_to_markets:Mapping[str,Tuple[str,...]]
    cross_venue_market_ids:Tuple[str,...]
    direct_market_ids:Tuple[str,...]
    propagated_market_ids:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"family_to_markets",_freeze_index(self.family_to_markets))
        object.__setattr__(self,"venue_to_markets",_freeze_index(self.venue_to_markets))
        for name in ("cross_venue_market_ids","direct_market_ids","propagated_market_ids"):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        if set(self.direct_market_ids)&set(self.propagated_market_ids):
            raise ValueError("direct and propagated market sets must not overlap")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_125_BUILD_ID:
            raise ValueError("lineage must belong to UMD-125")

    def markets_for_family(self,family_key:str)->Tuple[str,...]:
        return self.family_to_markets.get(family_key,())

    def markets_for_venue(self,venue_key:str)->Tuple[str,...]:
        return self.venue_to_markets.get(venue_key,())

    @property
    def matrix_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "family_to_markets":self.family_to_markets,
            "venue_to_markets":self.venue_to_markets,
            "cross_venue_market_ids":self.cross_venue_market_ids,
            "direct_market_ids":self.direct_market_ids,
            "propagated_market_ids":self.propagated_market_ids,
            "lineage":self.lineage,
        })

class ImpactCoverageMatrixBuilder:
    __slots__=()

    def build(
        self,
        family_projection:FamilyImpactProjection,
        cohort:CrossVenueImpactCohort,
        *,
        lineage:ImmutableLineage,
    )->ImpactCoverageMatrix:
        if not isinstance(family_projection,FamilyImpactProjection):
            raise TypeError("family_projection must be FamilyImpactProjection")
        if not isinstance(cohort,CrossVenueImpactCohort):
            raise TypeError("cohort must be CrossVenueImpactCohort")
        if family_projection.observation_hash!=cohort.observation_hash:
            raise ValueError("observation hashes do not match")

        family={}
        direct=set()
        propagated=set()
        for impact in family_projection.family_impacts:
            family[impact.family_key]=tuple(impact.impacted_market_ids)
            direct.update(impact.direct_market_ids)
            propagated.update(impact.propagated_market_ids)

        venue={}
        for market in cohort.markets:
            target=direct if market.direct else propagated
            target.add(market.canonical_market_id)
            for venue_key in market.venue_keys:
                venue.setdefault(venue_key,[]).append(market.canonical_market_id)

        for key,values in venue.items():
            venue[key]=tuple(sorted(set(values)))

        return ImpactCoverageMatrix(
            family_projection.observation_hash,
            family,
            venue,
            cohort.cross_venue_market_ids(),
            tuple(sorted(direct)),
            tuple(sorted(propagated)),
            lineage,
        )

def build_umd_125_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_125_BUILD_ID,"revision":UMD_125_REVISION,
        "schema_version":UMD_125_SCHEMA_VERSION,"upstream_builds":("UMD-121","UMD-124"),
        "mode":"deterministic_read_only_impact_coverage_matrix",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_125_impact_coverage_matrix()->bool:
    if verify_umd_124_cross_venue_impact_cohort() is not True:
        return False
    m=build_umd_125_certification_manifest()
    return m["build_id"]=="UMD-125" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
