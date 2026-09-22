from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_111_semantic_registry import SemanticRegistry
from .umd_129_market_topology import MarketTopologyRegistry
from .umd_154_change_boundary_expansion import ChangeBoundaryExpansion,verify_umd_154_change_boundary_expansion

UMD_155_BUILD_ID="UMD-155"
UMD_155_REVISION="UMD_155_CHANGE_STRUCTURAL_NEIGHBORHOOD_V1"
UMD_155_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ChangeStructuralNeighborhood:
    change_hash:str
    impacted_market_ids:Tuple[str,...]
    boundary_market_ids:Tuple[str,...]
    family_neighbor_ids:Tuple[str,...]
    topology_neighbor_ids:Tuple[str,...]
    all_market_ids:Tuple[str,...]
    relation_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        for name in (
            "impacted_market_ids","boundary_market_ids","family_neighbor_ids",
            "topology_neighbor_ids","all_market_ids"
        ):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        object.__setattr__(self,"relation_index",_freeze(self.relation_index))
        expected=tuple(sorted(set(
            self.impacted_market_ids+self.boundary_market_ids+
            self.family_neighbor_ids+self.topology_neighbor_ids
        )))
        if self.all_market_ids!=expected:
            raise ValueError("all_market_ids must equal union of neighborhood sets")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_155_BUILD_ID:
            raise ValueError("lineage must belong to UMD-155")
        if self.change_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include change hash")

    def markets_for_relation(self,relation:str)->Tuple[str,...]:
        return self.relation_index.get(relation,())

    @property
    def neighborhood_hash(self)->str:
        return deterministic_sha256({
            "change_hash":self.change_hash,
            "impacted_market_ids":self.impacted_market_ids,
            "boundary_market_ids":self.boundary_market_ids,
            "family_neighbor_ids":self.family_neighbor_ids,
            "topology_neighbor_ids":self.topology_neighbor_ids,
            "all_market_ids":self.all_market_ids,
            "relation_index":self.relation_index,
            "lineage":self.lineage,
        })

class ChangeStructuralNeighborhoodBuilder:
    __slots__=("semantic_registry","topology_registry")

    def __init__(self,semantic_registry:SemanticRegistry,topology_registry:MarketTopologyRegistry):
        if not isinstance(semantic_registry,SemanticRegistry):
            raise TypeError("semantic_registry must be SemanticRegistry")
        if not isinstance(topology_registry,MarketTopologyRegistry):
            raise TypeError("topology_registry must be MarketTopologyRegistry")
        self.semantic_registry=semantic_registry
        self.topology_registry=topology_registry

    def build(
        self,
        expansion:ChangeBoundaryExpansion,
        *,
        lineage:ImmutableLineage,
    )->ChangeStructuralNeighborhood:
        if not isinstance(expansion,ChangeBoundaryExpansion):
            raise TypeError("expansion must be ChangeBoundaryExpansion")

        seeds=set(expansion.impacted_market_ids)|set(expansion.adjacent_market_ids)
        family_neighbors=set()
        topology_neighbors=set()

        # Same semantic-family membership.
        for family in self.semantic_registry.families:
            if seeds.intersection(family.member_market_ids):
                family_neighbors.update(family.member_market_ids)

        # Same ladder or partition membership.
        for market_id in sorted(seeds):
            ladder_hashes=self.topology_registry.ladders_for_market(market_id)
            partition_hashes=self.topology_registry.partitions_for_market(market_id)
            for ladder in self.topology_registry.ladders:
                if ladder.ladder_hash in ladder_hashes:
                    topology_neighbors.update(r.canonical_market_id for r in ladder.rungs)
            for partition in self.topology_registry.partitions:
                if partition.partition_hash in partition_hashes:
                    topology_neighbors.update(m.canonical_market_id for m in partition.members)

        impacted=set(expansion.impacted_market_ids)
        boundary=set(expansion.adjacent_market_ids)
        family_neighbors.difference_update(impacted|boundary)
        topology_neighbors.difference_update(impacted|boundary)

        relation_index={
            "impacted":tuple(sorted(impacted)),
            "boundary":tuple(sorted(boundary)),
            "family-neighbor":tuple(sorted(family_neighbors)),
            "topology-neighbor":tuple(sorted(topology_neighbors)),
        }
        all_ids=tuple(sorted(impacted|boundary|family_neighbors|topology_neighbors))

        return ChangeStructuralNeighborhood(
            expansion.change_hash,
            tuple(sorted(impacted)),
            tuple(sorted(boundary)),
            tuple(sorted(family_neighbors)),
            tuple(sorted(topology_neighbors)),
            all_ids,
            relation_index,
            lineage,
        )

def build_umd_155_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_155_BUILD_ID,"revision":UMD_155_REVISION,
        "schema_version":UMD_155_SCHEMA_VERSION,"upstream_builds":("UMD-111","UMD-129","UMD-154"),
        "mode":"deterministic_read_only_change_structural_neighborhood",
        "semantics":"structural_context_only_no_predicted_impact",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_155_change_structural_neighborhood()->bool:
    if verify_umd_154_change_boundary_expansion() is not True:
        return False
    m=build_umd_155_certification_manifest()
    return m["build_id"]=="UMD-155" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
