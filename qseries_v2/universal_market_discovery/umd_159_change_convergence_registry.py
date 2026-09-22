from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_158_change_convergence_projection import ChangeConvergenceProjection,verify_umd_158_change_convergence_projection

UMD_159_BUILD_ID="UMD-159"
UMD_159_REVISION="UMD_159_CHANGE_CONVERGENCE_REGISTRY_V1"
UMD_159_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ChangeConvergenceRegistry:
    projections:Tuple[ChangeConvergenceProjection,...]
    market_index:Mapping[str,Tuple[str,...]]
    change_index:Mapping[str,Tuple[str,...]]
    dependency_index:Mapping[str,Tuple[str,...]]
    role_index:Mapping[str,Tuple[str,...]]
    constraint_type_index:Mapping[str,Tuple[str,...]]
    relation_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"projections",tuple(self.projections))
        for name in (
            "market_index","change_index","dependency_index","role_index",
            "constraint_type_index","relation_index"
        ):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.projections!=tuple(sorted(self.projections,key=lambda p:p.projection_hash)):
            raise ValueError("projections must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_159_BUILD_ID:
            raise ValueError("lineage must belong to UMD-159")
        required={p.projection_hash for p in self.projections}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every convergence projection hash")

    def convergence_hashes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.market_index.get(market_id,())

    def markets_for_change(self,change_hash:str)->Tuple[str,...]:
        return self.change_index.get(change_hash,())

    def markets_for_dependency(self,key:str)->Tuple[str,...]:
        return self.dependency_index.get(key,())

    def markets_for_role(self,role:str)->Tuple[str,...]:
        return self.role_index.get(role,())

    def markets_for_constraint_type(self,constraint_type:str)->Tuple[str,...]:
        return self.constraint_type_index.get(constraint_type,())

    def markets_for_relation(self,relation:str)->Tuple[str,...]:
        return self.relation_index.get(relation,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "projection_hashes":tuple(p.projection_hash for p in self.projections),
            "market_index":self.market_index,
            "change_index":self.change_index,
            "dependency_index":self.dependency_index,
            "role_index":self.role_index,
            "constraint_type_index":self.constraint_type_index,
            "relation_index":self.relation_index,
            "lineage":self.lineage,
        })

class ChangeConvergenceRegistryBuilder:
    __slots__=()

    def build(
        self,
        projections:Iterable[ChangeConvergenceProjection],
        *,
        lineage_factory,
    )->ChangeConvergenceRegistry:
        values=tuple(projections)
        if any(not isinstance(p,ChangeConvergenceProjection) for p in values):
            raise TypeError("projections must contain ChangeConvergenceProjection")
        values=tuple(sorted(values,key=lambda p:p.projection_hash))

        market={}
        change={}
        dependency={}
        role={}
        constraint={}
        relation={}

        for projection in values:
            for convergence in projection.convergences:
                market.setdefault(convergence.canonical_market_id,[]).append(convergence.convergence_hash)
                for change_hash in convergence.change_hashes:
                    change.setdefault(change_hash,[]).append(convergence.canonical_market_id)
                for key in convergence.dependency_keys:
                    dependency.setdefault(key,[]).append(convergence.canonical_market_id)
                for key in convergence.dependency_roles:
                    role.setdefault(key,[]).append(convergence.canonical_market_id)
                for key in convergence.constraint_types:
                    constraint.setdefault(key,[]).append(convergence.canonical_market_id)
                for key in convergence.relation_types:
                    relation.setdefault(key,[]).append(convergence.canonical_market_id)

        for index in (market,change,dependency,role,constraint,relation):
            for key,items in index.items():
                index[key]=tuple(sorted(set(items)))

        lineage=lineage_factory(tuple(p.projection_hash for p in values))
        return ChangeConvergenceRegistry(
            values,market,change,dependency,role,constraint,relation,lineage
        )

def build_umd_159_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_159_BUILD_ID,"revision":UMD_159_REVISION,
        "schema_version":UMD_159_SCHEMA_VERSION,"upstream_builds":("UMD-158",),
        "mode":"deterministic_read_only_change_convergence_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_159_change_convergence_registry()->bool:
    if verify_umd_158_change_convergence_projection() is not True:
        return False
    m=build_umd_159_certification_manifest()
    return m["build_id"]=="UMD-159" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
