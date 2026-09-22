from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_132_observation_routing import ObservationRoute,verify_umd_132_observation_routing

UMD_133_BUILD_ID="UMD-133"
UMD_133_REVISION="UMD_133_OBSERVATION_PRIORITY_PROFILE_V1"
UMD_133_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ObservationPriorityProfile:
    observation_id:str
    route_hash:str
    direct_dependency_count:int
    canonical_market_count:int
    family_count:int
    venue_count:int
    cross_venue_market_count:int
    unresolved_entity_count:int
    structural_span:int
    lineage:ImmutableLineage

    def __post_init__(self):
        for name in (
            "direct_dependency_count","canonical_market_count","family_count",
            "venue_count","cross_venue_market_count","unresolved_entity_count","structural_span"
        ):
            value=getattr(self,name)
            if not isinstance(value,int) or value<0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_133_BUILD_ID:
            raise ValueError("lineage must belong to UMD-133")
        if self.route_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include route hash")

    @property
    def profile_hash(self)->str:
        return deterministic_sha256({
            "observation_id":self.observation_id,
            "route_hash":self.route_hash,
            "direct_dependency_count":self.direct_dependency_count,
            "canonical_market_count":self.canonical_market_count,
            "family_count":self.family_count,
            "venue_count":self.venue_count,
            "cross_venue_market_count":self.cross_venue_market_count,
            "unresolved_entity_count":self.unresolved_entity_count,
            "structural_span":self.structural_span,
            "lineage":self.lineage,
        })

class ObservationPriorityProfiler:
    __slots__=()

    def build(self,route:ObservationRoute,*,lineage:ImmutableLineage)->ObservationPriorityProfile:
        if not isinstance(route,ObservationRoute):
            raise TypeError("route must be ObservationRoute")

        venue_sets={}
        for binding in route.venue_bindings:
            venue_sets.setdefault(binding.canonical_market_id,set()).add(binding.venue_key)

        cross_venue=sum(1 for venues in venue_sets.values() if len(venues)>1)
        dependency_count=len(route.matched_dependencies)
        market_count=len(route.market_ids)
        family_count=len(route.family_keys)
        venue_count=len(route.venues())
        unresolved_count=len(route.unresolved_entities)

        # Structural span is deliberately not a trading score. It is only a
        # deterministic measure of how broadly the observation touches the market universe.
        structural_span=dependency_count+market_count+family_count+venue_count+cross_venue

        return ObservationPriorityProfile(
            route.observation_id,
            route.route_hash,
            dependency_count,
            market_count,
            family_count,
            venue_count,
            cross_venue,
            unresolved_count,
            structural_span,
            lineage,
        )

def build_umd_133_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_133_BUILD_ID,"revision":UMD_133_REVISION,
        "schema_version":UMD_133_SCHEMA_VERSION,"upstream_builds":("UMD-132",),
        "mode":"deterministic_read_only_observation_structural_priority",
        "priority_semantics":"structural_reach_only_not_trade_value",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_133_observation_priority_profile()->bool:
    if verify_umd_132_observation_routing() is not True:
        return False
    m=build_umd_133_certification_manifest()
    return m["build_id"]=="UMD-133" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
