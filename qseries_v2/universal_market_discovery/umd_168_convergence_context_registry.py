from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_166_convergence_dependency_projection import ConvergenceDependencyProjection
from .umd_167_convergence_constraint_projection import ConvergenceConstraintProjection,verify_umd_167_convergence_constraint_projection

UMD_168_BUILD_ID="UMD-168"
UMD_168_REVISION="UMD_168_CONVERGENCE_CONTEXT_REGISTRY_V1"
UMD_168_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ConvergenceContextRegistry:
    dependency_projections:Tuple[ConvergenceDependencyProjection,...]
    constraint_projections:Tuple[ConvergenceConstraintProjection,...]
    market_index:Mapping[str,Tuple[str,...]]
    dependency_index:Mapping[str,Tuple[str,...]]
    role_index:Mapping[str,Tuple[str,...]]
    constraint_index:Mapping[str,Tuple[str,...]]
    relation_index:Mapping[str,Tuple[str,...]]
    change_type_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"dependency_projections",tuple(self.dependency_projections))
        object.__setattr__(self,"constraint_projections",tuple(self.constraint_projections))
        for name in (
            "market_index","dependency_index","role_index","constraint_index",
            "relation_index","change_type_index"
        ):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.dependency_projections!=tuple(sorted(self.dependency_projections,key=lambda p:p.projection_hash)):
            raise ValueError("dependency projections must be deterministically sorted")
        if self.constraint_projections!=tuple(sorted(self.constraint_projections,key=lambda p:p.projection_hash)):
            raise ValueError("constraint projections must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_168_BUILD_ID:
            raise ValueError("lineage must belong to UMD-168")
        required={p.projection_hash for p in self.dependency_projections}|{
            p.projection_hash for p in self.constraint_projections
        }
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every convergence context projection hash")

    def change_types_for_market(self,market_id:str)->Tuple[str,...]:
        return self.market_index.get(market_id,())
    def markets_for_dependency(self,key:str)->Tuple[str,...]:
        return self.dependency_index.get(key,())
    def markets_for_role(self,role:str)->Tuple[str,...]:
        return self.role_index.get(role,())
    def markets_for_constraint(self,constraint_type:str)->Tuple[str,...]:
        return self.constraint_index.get(constraint_type,())
    def markets_for_relation(self,relation:str)->Tuple[str,...]:
        return self.relation_index.get(relation,())
    def markets_for_change_type(self,change_type:str)->Tuple[str,...]:
        return self.change_type_index.get(change_type,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "dependency_projection_hashes":tuple(p.projection_hash for p in self.dependency_projections),
            "constraint_projection_hashes":tuple(p.projection_hash for p in self.constraint_projections),
            "market_index":self.market_index,
            "dependency_index":self.dependency_index,
            "role_index":self.role_index,
            "constraint_index":self.constraint_index,
            "relation_index":self.relation_index,
            "change_type_index":self.change_type_index,
            "lineage":self.lineage,
        })

class ConvergenceContextRegistryBuilder:
    __slots__=()

    def build(
        self,
        dependency_projections:Iterable[ConvergenceDependencyProjection],
        constraint_projections:Iterable[ConvergenceConstraintProjection],
        *,
        lineage_factory,
    )->ConvergenceContextRegistry:
        deps=tuple(dependency_projections)
        cons=tuple(constraint_projections)
        if any(not isinstance(p,ConvergenceDependencyProjection) for p in deps):
            raise TypeError("dependency_projections must contain ConvergenceDependencyProjection")
        if any(not isinstance(p,ConvergenceConstraintProjection) for p in cons):
            raise TypeError("constraint_projections must contain ConvergenceConstraintProjection")

        deps=tuple(sorted(deps,key=lambda p:p.projection_hash))
        cons=tuple(sorted(cons,key=lambda p:p.projection_hash))

        market={}; dependency={}; role={}; constraint={}; relation={}; change_type={}

        for projection in deps:
            for context in projection.contexts:
                market.setdefault(context.canonical_market_id,[]).extend(context.convergence_change_types)
                for key in context.dependency_keys:
                    dependency.setdefault(key,[]).append(context.canonical_market_id)
                for key in context.dependency_roles:
                    role.setdefault(key,[]).append(context.canonical_market_id)
                for key in context.convergence_change_types:
                    change_type.setdefault(key,[]).append(context.canonical_market_id)

        for projection in cons:
            for context in projection.contexts:
                market.setdefault(context.canonical_market_id,[]).extend(context.convergence_change_types)
                for key in context.constraint_types:
                    constraint.setdefault(key,[]).append(context.canonical_market_id)
                for key in context.relation_types:
                    relation.setdefault(key,[]).append(context.canonical_market_id)
                for key in context.convergence_change_types:
                    change_type.setdefault(key,[]).append(context.canonical_market_id)

        for index in (market,dependency,role,constraint,relation,change_type):
            for key,items in index.items():
                index[key]=tuple(sorted(set(items)))

        parents=tuple(p.projection_hash for p in deps)+tuple(p.projection_hash for p in cons)
        lineage=lineage_factory(parents)
        return ConvergenceContextRegistry(
            deps,cons,market,dependency,role,constraint,relation,change_type,lineage
        )

def build_umd_168_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_168_BUILD_ID,"revision":UMD_168_REVISION,
        "schema_version":UMD_168_SCHEMA_VERSION,"upstream_builds":("UMD-166","UMD-167"),
        "mode":"deterministic_read_only_convergence_context_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_168_convergence_context_registry()->bool:
    if verify_umd_167_convergence_constraint_projection() is not True:
        return False
    m=build_umd_168_certification_manifest()
    return m["build_id"]=="UMD-168" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
