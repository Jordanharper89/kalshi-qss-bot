from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_148_change_topology_projection import ChangeTopologyProjection
from .umd_149_change_cross_venue_coverage import ChangeCrossVenueCoverage,verify_umd_149_change_cross_venue_coverage

UMD_150_BUILD_ID="UMD-150"
UMD_150_REVISION="UMD_150_CHANGE_STRUCTURE_REGISTRY_V1"
UMD_150_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ChangeStructureRegistry:
    topology_projections:Tuple[ChangeTopologyProjection,...]
    venue_coverages:Tuple[ChangeCrossVenueCoverage,...]
    ladder_index:Mapping[str,Tuple[str,...]]
    partition_index:Mapping[str,Tuple[str,...]]
    cross_venue_market_index:Mapping[str,Tuple[str,...]]
    market_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"topology_projections",tuple(self.topology_projections))
        object.__setattr__(self,"venue_coverages",tuple(self.venue_coverages))
        for name in ("ladder_index","partition_index","cross_venue_market_index","market_index"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.topology_projections!=tuple(sorted(self.topology_projections,key=lambda p:(p.change_hash,p.projection_hash))):
            raise ValueError("topology projections must be deterministically sorted")
        if self.venue_coverages!=tuple(sorted(self.venue_coverages,key=lambda c:(c.change_hash,c.coverage_hash))):
            raise ValueError("venue coverages must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_150_BUILD_ID:
            raise ValueError("lineage must belong to UMD-150")
        required={p.projection_hash for p in self.topology_projections}|{c.coverage_hash for c in self.venue_coverages}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every structure artifact hash")

    def changes_for_ladder(self,key:str)->Tuple[str,...]:
        return self.ladder_index.get(key,())
    def changes_for_partition(self,key:str)->Tuple[str,...]:
        return self.partition_index.get(key,())
    def changes_for_cross_venue_market(self,key:str)->Tuple[str,...]:
        return self.cross_venue_market_index.get(key,())
    def changes_for_market(self,key:str)->Tuple[str,...]:
        return self.market_index.get(key,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "projection_hashes":tuple(p.projection_hash for p in self.topology_projections),
            "coverage_hashes":tuple(c.coverage_hash for c in self.venue_coverages),
            "ladder_index":self.ladder_index,
            "partition_index":self.partition_index,
            "cross_venue_market_index":self.cross_venue_market_index,
            "market_index":self.market_index,
            "lineage":self.lineage,
        })

class ChangeStructureRegistryBuilder:
    __slots__=()

    def build(
        self,
        projections:Iterable[ChangeTopologyProjection],
        coverages:Iterable[ChangeCrossVenueCoverage],
        *,
        lineage_factory,
    )->ChangeStructureRegistry:
        ps=tuple(projections)
        cs=tuple(coverages)
        if any(not isinstance(p,ChangeTopologyProjection) for p in ps):
            raise TypeError("projections must contain ChangeTopologyProjection")
        if any(not isinstance(c,ChangeCrossVenueCoverage) for c in cs):
            raise TypeError("coverages must contain ChangeCrossVenueCoverage")

        ps=tuple(sorted(ps,key=lambda p:(p.change_hash,p.projection_hash)))
        cs=tuple(sorted(cs,key=lambda c:(c.change_hash,c.coverage_hash)))

        ladder={}; partition={}; cross={}; market={}

        for p in ps:
            for key in p.ladder_hashes:
                ladder.setdefault(key,[]).append(p.change_hash)
            for key in p.partition_hashes:
                partition.setdefault(key,[]).append(p.change_hash)
            for key in p.market_ids:
                market.setdefault(key,[]).append(p.change_hash)

        for c in cs:
            for key in c.cross_venue_market_ids():
                cross.setdefault(key,[]).append(c.change_hash)
            for m in c.markets:
                market.setdefault(m.canonical_market_id,[]).append(c.change_hash)

        for index in (ladder,partition,cross,market):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        parents=tuple(p.projection_hash for p in ps)+tuple(c.coverage_hash for c in cs)
        lineage=lineage_factory(parents)
        return ChangeStructureRegistry(ps,cs,ladder,partition,cross,market,lineage)

def build_umd_150_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_150_BUILD_ID,"revision":UMD_150_REVISION,
        "schema_version":UMD_150_SCHEMA_VERSION,"upstream_builds":("UMD-148","UMD-149"),
        "mode":"deterministic_read_only_change_structure_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_150_change_structure_registry()->bool:
    if verify_umd_149_change_cross_venue_coverage() is not True:
        return False
    m=build_umd_150_certification_manifest()
    return m["build_id"]=="UMD-150" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
