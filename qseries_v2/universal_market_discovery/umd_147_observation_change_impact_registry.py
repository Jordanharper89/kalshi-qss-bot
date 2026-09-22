from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_146_observation_change_impact_surface import ObservationChangeImpactSurface,verify_umd_146_observation_change_impact_surface

UMD_147_BUILD_ID="UMD-147"
UMD_147_REVISION="UMD_147_OBSERVATION_CHANGE_IMPACT_REGISTRY_V1"
UMD_147_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ObservationChangeImpactRegistry:
    surfaces:Tuple[ObservationChangeImpactSurface,...]
    market_index:Mapping[str,Tuple[str,...]]
    family_index:Mapping[str,Tuple[str,...]]
    venue_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"surfaces",tuple(self.surfaces))
        for name in ("market_index","family_index","venue_index"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.surfaces!=tuple(sorted(self.surfaces,key=lambda s:s.surface_hash)):
            raise ValueError("surfaces must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_147_BUILD_ID:
            raise ValueError("lineage must belong to UMD-147")
        required={s.surface_hash for s in self.surfaces}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every surface hash")

    def change_hashes_for_market(self,key:str)->Tuple[str,...]:
        return self.market_index.get(key,())
    def change_hashes_for_family(self,key:str)->Tuple[str,...]:
        return self.family_index.get(key,())
    def change_hashes_for_venue(self,key:str)->Tuple[str,...]:
        return self.venue_index.get(key,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "surface_hashes":tuple(s.surface_hash for s in self.surfaces),
            "market_index":self.market_index,
            "family_index":self.family_index,
            "venue_index":self.venue_index,
            "lineage":self.lineage,
        })

class ObservationChangeImpactRegistryBuilder:
    __slots__=()

    def build(self,surfaces:Iterable[ObservationChangeImpactSurface],*,lineage_factory)->ObservationChangeImpactRegistry:
        values=tuple(surfaces)
        if any(not isinstance(s,ObservationChangeImpactSurface) for s in values):
            raise TypeError("surfaces must contain ObservationChangeImpactSurface")
        values=tuple(sorted(values,key=lambda s:s.surface_hash))

        market={}; family={}; venue={}

        for surface in values:
            for key,changes in surface.market_to_changes.items():
                market.setdefault(key,[]).extend(changes)
            for key,changes in surface.family_to_changes.items():
                family.setdefault(key,[]).extend(changes)
            for key,changes in surface.venue_to_changes.items():
                venue.setdefault(key,[]).extend(changes)

        for index in (market,family,venue):
            for key,changes in index.items():
                index[key]=tuple(sorted(set(changes)))

        lineage=lineage_factory(tuple(s.surface_hash for s in values))
        return ObservationChangeImpactRegistry(values,market,family,venue,lineage)

def build_umd_147_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_147_BUILD_ID,"revision":UMD_147_REVISION,
        "schema_version":UMD_147_SCHEMA_VERSION,"upstream_builds":("UMD-146",),
        "mode":"deterministic_read_only_observation_change_impact_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_147_observation_change_impact_registry()->bool:
    if verify_umd_146_observation_change_impact_surface() is not True:
        return False
    m=build_umd_147_certification_manifest()
    return m["build_id"]=="UMD-147" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
