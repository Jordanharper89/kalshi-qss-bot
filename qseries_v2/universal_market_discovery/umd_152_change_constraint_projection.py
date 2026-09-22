from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_113_market_constraints import MarketConstraintGraph
from .umd_151_change_dependency_projection import ChangeDependencyProjection,verify_umd_151_change_dependency_projection

UMD_152_BUILD_ID="UMD-152"
UMD_152_REVISION="UMD_152_CHANGE_CONSTRAINT_PROJECTION_V1"
UMD_152_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ChangeConstraintBinding:
    source_market_id:str
    target_market_id:str
    constraint_type:str
    basis:str
    source_impacted:bool
    target_impacted:bool
    constraint_hash:str

    @property
    def boundary(self)->bool:
        return self.source_impacted != self.target_impacted

    @property
    def internal(self)->bool:
        return self.source_impacted and self.target_impacted

    @property
    def binding_hash(self)->str:
        return deterministic_sha256({
            "source_market_id":self.source_market_id,
            "target_market_id":self.target_market_id,
            "constraint_type":self.constraint_type,
            "basis":self.basis,
            "source_impacted":self.source_impacted,
            "target_impacted":self.target_impacted,
            "constraint_hash":self.constraint_hash,
        })

@dataclass(frozen=True,slots=True)
class ChangeConstraintProjection:
    change_hash:str
    impacted_market_ids:Tuple[str,...]
    constraints:Tuple[ChangeConstraintBinding,...]
    internal_constraint_hashes:Tuple[str,...]
    boundary_constraint_hashes:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        for name in ("impacted_market_ids","internal_constraint_hashes","boundary_constraint_hashes"):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        object.__setattr__(self,"constraints",tuple(self.constraints))
        if self.constraints!=tuple(sorted(
            self.constraints,
            key=lambda c:(c.source_market_id,c.target_market_id,c.constraint_type,c.basis,c.constraint_hash)
        )):
            raise ValueError("constraints must be deterministically sorted")
        if set(self.internal_constraint_hashes)&set(self.boundary_constraint_hashes):
            raise ValueError("constraint cannot be both internal and boundary")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_152_BUILD_ID:
            raise ValueError("lineage must belong to UMD-152")
        if self.change_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include change hash")

    def constraints_of_type(self,constraint_type:str)->Tuple[ChangeConstraintBinding,...]:
        return tuple(c for c in self.constraints if c.constraint_type==constraint_type)

    @property
    def projection_hash(self)->str:
        return deterministic_sha256({
            "change_hash":self.change_hash,
            "impacted_market_ids":self.impacted_market_ids,
            "constraint_binding_hashes":tuple(c.binding_hash for c in self.constraints),
            "internal_constraint_hashes":self.internal_constraint_hashes,
            "boundary_constraint_hashes":self.boundary_constraint_hashes,
            "lineage":self.lineage,
        })

class ChangeConstraintProjector:
    __slots__=("graph",)

    def __init__(self,graph:MarketConstraintGraph):
        if not isinstance(graph,MarketConstraintGraph):
            raise TypeError("graph must be MarketConstraintGraph")
        self.graph=graph

    def project(
        self,
        dependency_projection:ChangeDependencyProjection,
        *,
        lineage:ImmutableLineage,
    )->ChangeConstraintProjection:
        if not isinstance(dependency_projection,ChangeDependencyProjection):
            raise TypeError("dependency_projection must be ChangeDependencyProjection")

        impacted=set(dependency_projection.market_ids)
        bindings=[]
        internal=[]
        boundary=[]

        for constraint in self.graph.constraints:
            source_hit=constraint.source_market_id in impacted
            target_hit=constraint.target_market_id in impacted
            if not source_hit and not target_hit:
                continue
            binding=ChangeConstraintBinding(
                constraint.source_market_id,
                constraint.target_market_id,
                constraint.constraint_type,
                constraint.basis,
                source_hit,
                target_hit,
                constraint.constraint_hash,
            )
            bindings.append(binding)
            if binding.internal:
                internal.append(constraint.constraint_hash)
            elif binding.boundary:
                boundary.append(constraint.constraint_hash)

        bindings.sort(key=lambda c:(c.source_market_id,c.target_market_id,c.constraint_type,c.basis,c.constraint_hash))
        return ChangeConstraintProjection(
            dependency_projection.change_hash,
            dependency_projection.market_ids,
            tuple(bindings),
            tuple(sorted(set(internal))),
            tuple(sorted(set(boundary))),
            lineage,
        )

def build_umd_152_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_152_BUILD_ID,"revision":UMD_152_REVISION,
        "schema_version":UMD_152_SCHEMA_VERSION,"upstream_builds":("UMD-113","UMD-151"),
        "mode":"deterministic_read_only_change_constraint_projection",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_152_change_constraint_projection()->bool:
    if verify_umd_151_change_dependency_projection() is not True:
        return False
    m=build_umd_152_certification_manifest()
    return m["build_id"]=="UMD-152" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
