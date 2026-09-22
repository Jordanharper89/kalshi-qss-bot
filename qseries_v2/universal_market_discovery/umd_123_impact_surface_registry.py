from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_121_impact_family_projection import FamilyImpactProjection
from .umd_122_impact_venue_projection import VenueImpactProjection, verify_umd_122_impact_venue_projection

UMD_123_BUILD_ID="UMD-123"
UMD_123_REVISION="UMD_123_IMPACT_SURFACE_REGISTRY_V1"
UMD_123_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze_index(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ImpactSurface:
    observation_hash:str
    family_keys:Tuple[str,...]
    canonical_market_ids:Tuple[str,...]
    venue_keys:Tuple[str,...]
    family_projection_hash:str
    venue_projection_hash:str

    def __post_init__(self):
        for name in ("family_keys","canonical_market_ids","venue_keys"):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)

    @property
    def surface_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "family_keys":self.family_keys,
            "canonical_market_ids":self.canonical_market_ids,
            "venue_keys":self.venue_keys,
            "family_projection_hash":self.family_projection_hash,
            "venue_projection_hash":self.venue_projection_hash,
        })

@dataclass(frozen=True,slots=True)
class ImpactSurfaceRegistry:
    surfaces:Tuple[ImpactSurface,...]
    observation_index:Mapping[str,Tuple[str,...]]
    family_index:Mapping[str,Tuple[str,...]]
    venue_index:Mapping[str,Tuple[str,...]]
    market_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"surfaces",tuple(self.surfaces))
        for name in ("observation_index","family_index","venue_index","market_index"):
            object.__setattr__(self,name,_freeze_index(getattr(self,name)))
        if tuple(sorted(self.surfaces,key=lambda s:(s.observation_hash,s.surface_hash)))!=self.surfaces:
            raise ValueError("surfaces must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_123_BUILD_ID:
            raise ValueError("lineage must belong to UMD-123")
        required={s.surface_hash for s in self.surfaces}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every surface hash")

    def observations_for_venue(self,venue_key:str)->Tuple[str,...]:
        return self.venue_index.get(venue_key,())

    def observations_for_family(self,family_key:str)->Tuple[str,...]:
        return self.family_index.get(family_key,())

    def observations_for_market(self,canonical_market_id:str)->Tuple[str,...]:
        return self.market_index.get(canonical_market_id,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "surface_hashes":tuple(s.surface_hash for s in self.surfaces),
            "observation_index":self.observation_index,
            "family_index":self.family_index,
            "venue_index":self.venue_index,
            "market_index":self.market_index,
            "lineage":self.lineage,
        })

class ImpactSurfaceRegistryBuilder:
    __slots__=()

    def build(
        self,
        pairs:Iterable[tuple[FamilyImpactProjection,VenueImpactProjection]],
        *,
        lineage_factory,
    )->ImpactSurfaceRegistry:
        surfaces=[]
        observation={}
        family={}
        venue={}
        market={}

        for family_projection,venue_projection in pairs:
            if not isinstance(family_projection,FamilyImpactProjection):
                raise TypeError("family projection must be FamilyImpactProjection")
            if not isinstance(venue_projection,VenueImpactProjection):
                raise TypeError("venue projection must be VenueImpactProjection")
            if family_projection.observation_hash!=venue_projection.observation_hash:
                raise ValueError("projection observation hashes do not match")

            family_keys=tuple(sorted(x.family_key for x in family_projection.family_impacts))
            markets=set(family_projection.unmatched_market_ids)
            for impact in family_projection.family_impacts:
                markets.update(impact.impacted_market_ids)
            venue_keys=venue_projection.venues()

            surface=ImpactSurface(
                family_projection.observation_hash,
                family_keys,
                tuple(sorted(markets)),
                venue_keys,
                family_projection.projection_hash,
                venue_projection.projection_hash,
            )
            surfaces.append(surface)

            observation.setdefault(surface.observation_hash,[]).append(surface.surface_hash)
            for key in surface.family_keys:
                family.setdefault(key,[]).append(surface.observation_hash)
            for key in surface.venue_keys:
                venue.setdefault(key,[]).append(surface.observation_hash)
            for key in surface.canonical_market_ids:
                market.setdefault(key,[]).append(surface.observation_hash)

        surfaces.sort(key=lambda s:(s.observation_hash,s.surface_hash))
        for index in (observation,family,venue,market):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        lineage=lineage_factory(tuple(s.surface_hash for s in surfaces))
        return ImpactSurfaceRegistry(tuple(surfaces),observation,family,venue,market,lineage)

def build_umd_123_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_123_BUILD_ID,"revision":UMD_123_REVISION,
        "schema_version":UMD_123_SCHEMA_VERSION,"upstream_builds":("UMD-121","UMD-122"),
        "mode":"deterministic_read_only_impact_surface_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_123_impact_surface_registry()->bool:
    if verify_umd_122_impact_venue_projection() is not True:
        return False
    m=build_umd_123_certification_manifest()
    return m["build_id"]=="UMD-123" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
