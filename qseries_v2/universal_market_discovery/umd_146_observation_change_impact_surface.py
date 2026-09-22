from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_145_observation_change_routing import ObservationChangeRouting,verify_umd_145_observation_change_routing

UMD_146_BUILD_ID="UMD-146"
UMD_146_REVISION="UMD_146_OBSERVATION_CHANGE_IMPACT_SURFACE_V1"
UMD_146_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ObservationChangeImpactSurface:
    routing_hash:str
    market_to_changes:Mapping[str,Tuple[str,...]]
    family_to_changes:Mapping[str,Tuple[str,...]]
    venue_to_changes:Mapping[str,Tuple[str,...]]
    change_to_markets:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        for name in ("market_to_changes","family_to_changes","venue_to_changes","change_to_markets"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_146_BUILD_ID:
            raise ValueError("lineage must belong to UMD-146")
        if self.routing_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include change routing hash")

    def changes_for_market(self,key:str)->Tuple[str,...]:
        return self.market_to_changes.get(key,())
    def changes_for_family(self,key:str)->Tuple[str,...]:
        return self.family_to_changes.get(key,())
    def changes_for_venue(self,key:str)->Tuple[str,...]:
        return self.venue_to_changes.get(key,())
    def markets_for_change(self,change_hash:str)->Tuple[str,...]:
        return self.change_to_markets.get(change_hash,())

    @property
    def surface_hash(self)->str:
        return deterministic_sha256({
            "routing_hash":self.routing_hash,
            "market_to_changes":self.market_to_changes,
            "family_to_changes":self.family_to_changes,
            "venue_to_changes":self.venue_to_changes,
            "change_to_markets":self.change_to_markets,
            "lineage":self.lineage,
        })

class ObservationChangeImpactSurfaceBuilder:
    __slots__=()

    def build(self,routing:ObservationChangeRouting,*,lineage:ImmutableLineage)->ObservationChangeImpactSurface:
        if not isinstance(routing,ObservationChangeRouting):
            raise TypeError("routing must be ObservationChangeRouting")
        market={}; family={}; venue={}; change_to_markets={}

        for route in routing.routes:
            change_to_markets[route.change_hash]=route.market_ids
            for key in route.market_ids:
                market.setdefault(key,[]).append(route.change_hash)
            for key in route.family_keys:
                family.setdefault(key,[]).append(route.change_hash)
            for key in route.venue_keys:
                venue.setdefault(key,[]).append(route.change_hash)

        for index in (market,family,venue):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        return ObservationChangeImpactSurface(
            routing.routing_hash,market,family,venue,change_to_markets,lineage
        )

def build_umd_146_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_146_BUILD_ID,"revision":UMD_146_REVISION,
        "schema_version":UMD_146_SCHEMA_VERSION,"upstream_builds":("UMD-145",),
        "mode":"deterministic_read_only_observation_change_impact_surface",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_146_observation_change_impact_surface()->bool:
    if verify_umd_145_observation_change_routing() is not True:
        return False
    m=build_umd_146_certification_manifest()
    return m["build_id"]=="UMD-146" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
