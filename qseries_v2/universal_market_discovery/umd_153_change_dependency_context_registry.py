from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_151_change_dependency_projection import ChangeDependencyProjection
from .umd_152_change_constraint_projection import ChangeConstraintProjection,verify_umd_152_change_constraint_projection

UMD_153_BUILD_ID="UMD-153"
UMD_153_REVISION="UMD_153_CHANGE_DEPENDENCY_CONTEXT_REGISTRY_V1"
UMD_153_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ChangeDependencyContextRegistry:
    dependency_projections:Tuple[ChangeDependencyProjection,...]
    constraint_projections:Tuple[ChangeConstraintProjection,...]
    dependency_index:Mapping[str,Tuple[str,...]]
    role_index:Mapping[str,Tuple[str,...]]
    constraint_type_index:Mapping[str,Tuple[str,...]]
    market_index:Mapping[str,Tuple[str,...]]
    boundary_market_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"dependency_projections",tuple(self.dependency_projections))
        object.__setattr__(self,"constraint_projections",tuple(self.constraint_projections))
        for name in ("dependency_index","role_index","constraint_type_index","market_index","boundary_market_index"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.dependency_projections!=tuple(sorted(
            self.dependency_projections,key=lambda p:(p.change_hash,p.projection_hash)
        )):
            raise ValueError("dependency projections must be deterministically sorted")
        if self.constraint_projections!=tuple(sorted(
            self.constraint_projections,key=lambda p:(p.change_hash,p.projection_hash)
        )):
            raise ValueError("constraint projections must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_153_BUILD_ID:
            raise ValueError("lineage must belong to UMD-153")
        required={p.projection_hash for p in self.dependency_projections}|{
            p.projection_hash for p in self.constraint_projections
        }
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every dependency and constraint projection hash")

    def changes_for_dependency(self,kind:str,key:str)->Tuple[str,...]:
        return self.dependency_index.get(kind+"="+key,())

    def changes_for_role(self,role:str)->Tuple[str,...]:
        return self.role_index.get(role,())

    def changes_for_constraint_type(self,constraint_type:str)->Tuple[str,...]:
        return self.constraint_type_index.get(constraint_type,())

    def changes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.market_index.get(market_id,())

    def boundary_changes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.boundary_market_index.get(market_id,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "dependency_projection_hashes":tuple(p.projection_hash for p in self.dependency_projections),
            "constraint_projection_hashes":tuple(p.projection_hash for p in self.constraint_projections),
            "dependency_index":self.dependency_index,
            "role_index":self.role_index,
            "constraint_type_index":self.constraint_type_index,
            "market_index":self.market_index,
            "boundary_market_index":self.boundary_market_index,
            "lineage":self.lineage,
        })

class ChangeDependencyContextRegistryBuilder:
    __slots__=()

    def build(
        self,
        dependency_projections:Iterable[ChangeDependencyProjection],
        constraint_projections:Iterable[ChangeConstraintProjection],
        *,
        lineage_factory,
    )->ChangeDependencyContextRegistry:
        deps=tuple(dependency_projections)
        cons=tuple(constraint_projections)
        if any(not isinstance(p,ChangeDependencyProjection) for p in deps):
            raise TypeError("dependency_projections must contain ChangeDependencyProjection")
        if any(not isinstance(p,ChangeConstraintProjection) for p in cons):
            raise TypeError("constraint_projections must contain ChangeConstraintProjection")

        deps=tuple(sorted(deps,key=lambda p:(p.change_hash,p.projection_hash)))
        cons=tuple(sorted(cons,key=lambda p:(p.change_hash,p.projection_hash)))

        dep_index={}
        role_index={}
        constraint_index={}
        market_index={}
        boundary_index={}

        for p in deps:
            for binding in p.bindings:
                dep_index.setdefault(binding.kind+"="+binding.key,[]).append(p.change_hash)
                role_index.setdefault(binding.role,[]).append(p.change_hash)
                market_index.setdefault(binding.canonical_market_id,[]).append(p.change_hash)
            for market_id in p.market_ids:
                market_index.setdefault(market_id,[]).append(p.change_hash)

        for p in cons:
            for binding in p.constraints:
                constraint_index.setdefault(binding.constraint_type,[]).append(p.change_hash)
                market_index.setdefault(binding.source_market_id,[]).append(p.change_hash)
                market_index.setdefault(binding.target_market_id,[]).append(p.change_hash)
                if binding.boundary:
                    impacted_market = (
                        binding.source_market_id if binding.source_impacted else binding.target_market_id
                    )
                    boundary_index.setdefault(impacted_market,[]).append(p.change_hash)

        for index in (dep_index,role_index,constraint_index,market_index,boundary_index):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        parents=tuple(p.projection_hash for p in deps)+tuple(p.projection_hash for p in cons)
        lineage=lineage_factory(parents)
        return ChangeDependencyContextRegistry(
            deps,cons,dep_index,role_index,constraint_index,market_index,boundary_index,lineage
        )

def build_umd_153_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_153_BUILD_ID,"revision":UMD_153_REVISION,
        "schema_version":UMD_153_SCHEMA_VERSION,"upstream_builds":("UMD-151","UMD-152"),
        "mode":"deterministic_read_only_change_dependency_context_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_153_change_dependency_context_registry()->bool:
    if verify_umd_152_change_constraint_projection() is not True:
        return False
    m=build_umd_153_certification_manifest()
    return m["build_id"]=="UMD-153" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
