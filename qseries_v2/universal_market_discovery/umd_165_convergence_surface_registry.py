from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_163_convergence_topology_projection import ConvergenceTopologyProjection
from .umd_164_convergence_venue_projection import ConvergenceVenueProjection,verify_umd_164_convergence_venue_projection

UMD_165_BUILD_ID="UMD-165"
UMD_165_REVISION="UMD_165_CONVERGENCE_SURFACE_REGISTRY_V1"
UMD_165_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ConvergenceSurfaceRegistry:
    topology_projections:Tuple[ConvergenceTopologyProjection,...]
    venue_projections:Tuple[ConvergenceVenueProjection,...]
    market_index:Mapping[str,Tuple[str,...]]
    ladder_index:Mapping[str,Tuple[str,...]]
    partition_index:Mapping[str,Tuple[str,...]]
    venue_index:Mapping[str,Tuple[str,...]]
    change_type_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"topology_projections",tuple(self.topology_projections))
        object.__setattr__(self,"venue_projections",tuple(self.venue_projections))
        for name in ("market_index","ladder_index","partition_index","venue_index","change_type_index"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.topology_projections!=tuple(sorted(self.topology_projections,key=lambda p:p.projection_hash)):
            raise ValueError("topology projections must be deterministically sorted")
        if self.venue_projections!=tuple(sorted(self.venue_projections,key=lambda p:p.projection_hash)):
            raise ValueError("venue projections must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_165_BUILD_ID:
            raise ValueError("lineage must belong to UMD-165")
        required={p.projection_hash for p in self.topology_projections}|{p.projection_hash for p in self.venue_projections}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every convergence surface projection hash")

    def change_types_for_market(self,market_id:str)->Tuple[str,...]:
        return self.market_index.get(market_id,())

    def markets_for_ladder(self,ladder_hash:str)->Tuple[str,...]:
        return self.ladder_index.get(ladder_hash,())

    def markets_for_partition(self,partition_hash:str)->Tuple[str,...]:
        return self.partition_index.get(partition_hash,())

    def markets_for_venue(self,venue_key:str)->Tuple[str,...]:
        return self.venue_index.get(venue_key,())

    def markets_for_change_type(self,change_type:str)->Tuple[str,...]:
        return self.change_type_index.get(change_type,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "topology_projection_hashes":tuple(p.projection_hash for p in self.topology_projections),
            "venue_projection_hashes":tuple(p.projection_hash for p in self.venue_projections),
            "market_index":self.market_index,
            "ladder_index":self.ladder_index,
            "partition_index":self.partition_index,
            "venue_index":self.venue_index,
            "change_type_index":self.change_type_index,
            "lineage":self.lineage,
        })

class ConvergenceSurfaceRegistryBuilder:
    __slots__=()

    def build(
        self,
        topology_projections:Iterable[ConvergenceTopologyProjection],
        venue_projections:Iterable[ConvergenceVenueProjection],
        *,
        lineage_factory,
    )->ConvergenceSurfaceRegistry:
        tps=tuple(topology_projections)
        vps=tuple(venue_projections)
        if any(not isinstance(p,ConvergenceTopologyProjection) for p in tps):
            raise TypeError("topology_projections must contain ConvergenceTopologyProjection")
        if any(not isinstance(p,ConvergenceVenueProjection) for p in vps):
            raise TypeError("venue_projections must contain ConvergenceVenueProjection")

        tps=tuple(sorted(tps,key=lambda p:p.projection_hash))
        vps=tuple(sorted(vps,key=lambda p:p.projection_hash))

        market={}; ladder={}; partition={}; venue={}; change_type={}

        for p in tps:
            for market_id,types in p.market_to_change_types.items():
                market.setdefault(market_id,[]).extend(types)
                for t in types:
                    change_type.setdefault(t,[]).append(market_id)
            for market_id,hashes in p.market_to_ladders.items():
                for h in hashes:
                    ladder.setdefault(h,[]).append(market_id)
            for market_id,hashes in p.market_to_partitions.items():
                for h in hashes:
                    partition.setdefault(h,[]).append(market_id)

        for p in vps:
            for binding in p.bindings:
                venue.setdefault(binding.venue_key,[]).append(binding.canonical_market_id)
                market.setdefault(binding.canonical_market_id,[]).extend(binding.change_types)
                for t in binding.change_types:
                    change_type.setdefault(t,[]).append(binding.canonical_market_id)

        for index in (market,ladder,partition,venue,change_type):
            for key,items in index.items():
                index[key]=tuple(sorted(set(items)))

        parents=tuple(p.projection_hash for p in tps)+tuple(p.projection_hash for p in vps)
        lineage=lineage_factory(parents)
        return ConvergenceSurfaceRegistry(tps,vps,market,ladder,partition,venue,change_type,lineage)

def build_umd_165_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_165_BUILD_ID,"revision":UMD_165_REVISION,
        "schema_version":UMD_165_SCHEMA_VERSION,"upstream_builds":("UMD-163","UMD-164"),
        "mode":"deterministic_read_only_convergence_surface_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_165_convergence_surface_registry()->bool:
    if verify_umd_164_convergence_venue_projection() is not True:
        return False
    m=build_umd_165_certification_manifest()
    return m["build_id"]=="UMD-165" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
