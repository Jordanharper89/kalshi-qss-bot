from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_155_change_structural_neighborhood import ChangeStructuralNeighborhood,verify_umd_155_change_structural_neighborhood

UMD_156_BUILD_ID="UMD-156"
UMD_156_REVISION="UMD_156_CHANGE_MARKET_CONTEXT_REGISTRY_V1"
UMD_156_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

RELATION_TYPES=("impacted","boundary","family-neighbor","topology-neighbor")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ChangeMarketContextRegistry:
    neighborhoods:Tuple[ChangeStructuralNeighborhood,...]
    market_index:Mapping[str,Tuple[str,...]]
    impacted_index:Mapping[str,Tuple[str,...]]
    boundary_index:Mapping[str,Tuple[str,...]]
    family_neighbor_index:Mapping[str,Tuple[str,...]]
    topology_neighbor_index:Mapping[str,Tuple[str,...]]
    change_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"neighborhoods",tuple(self.neighborhoods))
        for name in (
            "market_index","impacted_index","boundary_index",
            "family_neighbor_index","topology_neighbor_index","change_index"
        ):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.neighborhoods!=tuple(sorted(
            self.neighborhoods,key=lambda n:(n.change_hash,n.neighborhood_hash)
        )):
            raise ValueError("neighborhoods must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_156_BUILD_ID:
            raise ValueError("lineage must belong to UMD-156")
        required={n.neighborhood_hash for n in self.neighborhoods}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every neighborhood hash")

    def changes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.market_index.get(market_id,())

    def impacted_changes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.impacted_index.get(market_id,())

    def boundary_changes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.boundary_index.get(market_id,())

    def family_neighbor_changes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.family_neighbor_index.get(market_id,())

    def topology_neighbor_changes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.topology_neighbor_index.get(market_id,())

    def markets_for_change(self,change_hash:str)->Tuple[str,...]:
        return self.change_index.get(change_hash,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "neighborhood_hashes":tuple(n.neighborhood_hash for n in self.neighborhoods),
            "market_index":self.market_index,
            "impacted_index":self.impacted_index,
            "boundary_index":self.boundary_index,
            "family_neighbor_index":self.family_neighbor_index,
            "topology_neighbor_index":self.topology_neighbor_index,
            "change_index":self.change_index,
            "lineage":self.lineage,
        })

class ChangeMarketContextRegistryBuilder:
    __slots__=()

    def build(
        self,
        neighborhoods:Iterable[ChangeStructuralNeighborhood],
        *,
        lineage_factory,
    )->ChangeMarketContextRegistry:
        values=tuple(neighborhoods)
        if any(not isinstance(n,ChangeStructuralNeighborhood) for n in values):
            raise TypeError("neighborhoods must contain ChangeStructuralNeighborhood")
        values=tuple(sorted(values,key=lambda n:(n.change_hash,n.neighborhood_hash)))

        market={}
        impacted={}
        boundary={}
        family={}
        topology={}
        change={}

        for n in values:
            change[n.change_hash]=n.all_market_ids
            for market_id in n.all_market_ids:
                market.setdefault(market_id,[]).append(n.change_hash)
            for market_id in n.impacted_market_ids:
                impacted.setdefault(market_id,[]).append(n.change_hash)
            for market_id in n.boundary_market_ids:
                boundary.setdefault(market_id,[]).append(n.change_hash)
            for market_id in n.family_neighbor_ids:
                family.setdefault(market_id,[]).append(n.change_hash)
            for market_id in n.topology_neighbor_ids:
                topology.setdefault(market_id,[]).append(n.change_hash)

        for index in (market,impacted,boundary,family,topology):
            for key,items in index.items():
                index[key]=tuple(sorted(set(items)))

        lineage=lineage_factory(tuple(n.neighborhood_hash for n in values))
        return ChangeMarketContextRegistry(
            values,market,impacted,boundary,family,topology,change,lineage
        )

def build_umd_156_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_156_BUILD_ID,"revision":UMD_156_REVISION,
        "schema_version":UMD_156_SCHEMA_VERSION,"upstream_builds":("UMD-155",),
        "mode":"deterministic_read_only_change_market_context_registry",
        "relation_types":RELATION_TYPES,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_156_change_market_context_registry()->bool:
    if verify_umd_155_change_structural_neighborhood() is not True:
        return False
    m=build_umd_156_certification_manifest()
    return m["build_id"]=="UMD-156" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
