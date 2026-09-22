from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_152_change_constraint_projection import ChangeConstraintProjection,verify_umd_152_change_constraint_projection

UMD_154_BUILD_ID="UMD-154"
UMD_154_REVISION="UMD_154_CHANGE_BOUNDARY_EXPANSION_V1"
UMD_154_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ChangeBoundaryNeighbor:
    impacted_market_id:str
    adjacent_market_id:str
    constraint_type:str
    basis:str
    constraint_hash:str

    def __post_init__(self):
        if not self.impacted_market_id or not self.adjacent_market_id:
            raise ValueError("boundary neighbor market ids must be non-empty")
        if self.impacted_market_id==self.adjacent_market_id:
            raise ValueError("boundary neighbor markets must differ")

    @property
    def neighbor_hash(self)->str:
        return deterministic_sha256({
            "impacted_market_id":self.impacted_market_id,
            "adjacent_market_id":self.adjacent_market_id,
            "constraint_type":self.constraint_type,
            "basis":self.basis,
            "constraint_hash":self.constraint_hash,
        })

@dataclass(frozen=True,slots=True)
class ChangeBoundaryExpansion:
    change_hash:str
    impacted_market_ids:Tuple[str,...]
    adjacent_market_ids:Tuple[str,...]
    neighbors:Tuple[ChangeBoundaryNeighbor,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        for name in ("impacted_market_ids","adjacent_market_ids"):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        object.__setattr__(self,"neighbors",tuple(self.neighbors))
        if self.neighbors!=tuple(sorted(
            self.neighbors,
            key=lambda n:(n.impacted_market_id,n.adjacent_market_id,n.constraint_type,n.basis,n.constraint_hash)
        )):
            raise ValueError("neighbors must be deterministically sorted")
        if set(self.impacted_market_ids)&set(self.adjacent_market_ids):
            raise ValueError("adjacent markets must sit outside impacted set")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_154_BUILD_ID:
            raise ValueError("lineage must belong to UMD-154")
        if self.change_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include change hash")

    def neighbors_for(self,market_id:str)->Tuple[str,...]:
        return tuple(sorted({
            n.adjacent_market_id for n in self.neighbors if n.impacted_market_id==market_id
        }))

    @property
    def expansion_hash(self)->str:
        return deterministic_sha256({
            "change_hash":self.change_hash,
            "impacted_market_ids":self.impacted_market_ids,
            "adjacent_market_ids":self.adjacent_market_ids,
            "neighbor_hashes":tuple(n.neighbor_hash for n in self.neighbors),
            "lineage":self.lineage,
        })

class ChangeBoundaryExpander:
    __slots__=()

    def expand(
        self,
        projection:ChangeConstraintProjection,
        *,
        lineage:ImmutableLineage,
    )->ChangeBoundaryExpansion:
        if not isinstance(projection,ChangeConstraintProjection):
            raise TypeError("projection must be ChangeConstraintProjection")

        impacted=set(projection.impacted_market_ids)
        neighbors=[]
        adjacent=set()

        for binding in projection.constraints:
            if not binding.boundary:
                continue
            if binding.source_impacted:
                impacted_id=binding.source_market_id
                adjacent_id=binding.target_market_id
            else:
                impacted_id=binding.target_market_id
                adjacent_id=binding.source_market_id

            if impacted_id not in impacted or adjacent_id in impacted:
                raise ValueError("boundary binding inconsistent with impacted market set")

            adjacent.add(adjacent_id)
            neighbors.append(ChangeBoundaryNeighbor(
                impacted_id,
                adjacent_id,
                binding.constraint_type,
                binding.basis,
                binding.constraint_hash,
            ))

        neighbors.sort(
            key=lambda n:(n.impacted_market_id,n.adjacent_market_id,n.constraint_type,n.basis,n.constraint_hash)
        )
        return ChangeBoundaryExpansion(
            projection.change_hash,
            projection.impacted_market_ids,
            tuple(sorted(adjacent)),
            tuple(neighbors),
            lineage,
        )

def build_umd_154_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_154_BUILD_ID,"revision":UMD_154_REVISION,
        "schema_version":UMD_154_SCHEMA_VERSION,"upstream_builds":("UMD-152",),
        "mode":"deterministic_read_only_change_boundary_expansion",
        "semantics":"structural_adjacent_markets_only_not_predicted_impact",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_154_change_boundary_expansion()->bool:
    if verify_umd_152_change_constraint_projection() is not True:
        return False
    m=build_umd_154_certification_manifest()
    return m["build_id"]=="UMD-154" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
