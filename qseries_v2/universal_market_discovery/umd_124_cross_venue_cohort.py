from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_122_impact_venue_projection import VenueImpactProjection,VenueImpactBinding
from .umd_123_impact_surface_registry import verify_umd_123_impact_surface_registry

UMD_124_BUILD_ID="UMD-124"
UMD_124_REVISION="UMD_124_CROSS_VENUE_IMPACT_COHORT_V1"
UMD_124_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class MarketVenueCohort:
    canonical_market_id:str
    venue_keys:Tuple[str,...]
    venue_market_ids:Tuple[Tuple[str,str],...]
    direct:bool

    def __post_init__(self):
        object.__setattr__(self,"venue_keys",tuple(self.venue_keys))
        object.__setattr__(self,"venue_market_ids",tuple(self.venue_market_ids))
        if self.venue_keys!=tuple(sorted(set(self.venue_keys))):
            raise ValueError("venue_keys must be unique and sorted")
        if self.venue_market_ids!=tuple(sorted(set(self.venue_market_ids))):
            raise ValueError("venue_market_ids must be unique and sorted")
        if tuple(sorted({venue for venue,_ in self.venue_market_ids}))!=self.venue_keys:
            raise ValueError("venue_keys must match venue_market_ids")

    @property
    def cross_venue(self)->bool:
        return len(self.venue_keys)>1

    @property
    def cohort_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "venue_keys":self.venue_keys,
            "venue_market_ids":self.venue_market_ids,
            "direct":self.direct,
        })

@dataclass(frozen=True,slots=True)
class CrossVenueImpactCohort:
    observation_hash:str
    markets:Tuple[MarketVenueCohort,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"markets",tuple(self.markets))
        if self.markets!=tuple(sorted(self.markets,key=lambda m:(m.canonical_market_id,m.cohort_hash))):
            raise ValueError("markets must be deterministically sorted")
        if len({m.canonical_market_id for m in self.markets})!=len(self.markets):
            raise ValueError("duplicate canonical market cohort")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_124_BUILD_ID:
            raise ValueError("lineage must belong to UMD-124")

    def cross_venue_market_ids(self)->Tuple[str,...]:
        return tuple(m.canonical_market_id for m in self.markets if m.cross_venue)

    def for_market(self,canonical_market_id:str)->MarketVenueCohort|None:
        for market in self.markets:
            if market.canonical_market_id==canonical_market_id:
                return market
        return None

    @property
    def cohort_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "market_cohort_hashes":tuple(m.cohort_hash for m in self.markets),
            "lineage":self.lineage,
        })

class CrossVenueImpactCohortBuilder:
    __slots__=()

    def build(
        self,
        projection:VenueImpactProjection,
        *,
        lineage:ImmutableLineage,
    )->CrossVenueImpactCohort:
        if not isinstance(projection,VenueImpactProjection):
            raise TypeError("projection must be VenueImpactProjection")

        buckets={}
        for binding in projection.bindings:
            bucket=buckets.setdefault(binding.canonical_market_id,{"direct":binding.direct,"pairs":[]})
            if bucket["direct"] is not binding.direct:
                raise ValueError("direct flag mismatch across venue bindings for canonical market")
            bucket["pairs"].append((binding.venue_key,binding.venue_market_id))

        markets=[]
        for market_id,data in sorted(buckets.items()):
            pairs=tuple(sorted(set(data["pairs"])))
            venues=tuple(sorted({venue for venue,_ in pairs}))
            markets.append(MarketVenueCohort(market_id,venues,pairs,data["direct"]))

        return CrossVenueImpactCohort(
            projection.observation_hash,
            tuple(markets),
            lineage,
        )

def build_umd_124_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_124_BUILD_ID,"revision":UMD_124_REVISION,
        "schema_version":UMD_124_SCHEMA_VERSION,"upstream_builds":("UMD-122","UMD-123"),
        "mode":"deterministic_read_only_cross_venue_impact_cohort",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_124_cross_venue_impact_cohort()->bool:
    if verify_umd_123_impact_surface_registry() is not True:
        return False
    m=build_umd_124_certification_manifest()
    return m["build_id"]=="UMD-124" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
