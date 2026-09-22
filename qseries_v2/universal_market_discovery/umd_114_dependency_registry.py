from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_112_market_dependency import MarketDependencyProfile
from .umd_113_market_constraints import MarketConstraintGraph, verify_umd_113_market_constraint_graph

UMD_114_BUILD_ID="UMD-114"
UMD_114_REVISION="UMD_114_DEPENDENCY_REGISTRY_V1"
UMD_114_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze_index(source):
    return MappingProxyType({
        key:tuple(value)
        for key,value in sorted(source.items())
    })

@dataclass(frozen=True,slots=True)
class DependencyRegistry:
    profiles:Tuple[MarketDependencyProfile,...]
    constraint_graph_hash:str
    dependency_index:Mapping[str,Tuple[str,...]]
    role_index:Mapping[str,Tuple[str,...]]
    constraint_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"profiles",tuple(self.profiles))
        object.__setattr__(self,"dependency_index",_freeze_index(self.dependency_index))
        object.__setattr__(self,"role_index",_freeze_index(self.role_index))
        object.__setattr__(self,"constraint_index",_freeze_index(self.constraint_index))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_114_BUILD_ID:
            raise ValueError("lineage must belong to UMD-114")
        required={p.profile_hash for p in self.profiles}|{self.constraint_graph_hash}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include dependency profiles and constraint graph hash")

    def markets_for_dependency(self,kind:str,key:str)->Tuple[str,...]:
        return self.dependency_index.get(kind+"="+key,())

    def markets_for_role(self,role:str)->Tuple[str,...]:
        return self.role_index.get(role,())

    def markets_for_constraint(self,constraint_type:str)->Tuple[str,...]:
        return self.constraint_index.get(constraint_type,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "profile_hashes":tuple(p.profile_hash for p in self.profiles),
            "constraint_graph_hash":self.constraint_graph_hash,
            "dependency_index":self.dependency_index,
            "role_index":self.role_index,
            "constraint_index":self.constraint_index,
            "lineage":self.lineage,
        })

class DependencyRegistryBuilder:
    __slots__=()

    def build(
        self,
        profiles:Iterable[MarketDependencyProfile],
        constraint_graph:MarketConstraintGraph,
        *,
        lineage:ImmutableLineage,
    )->DependencyRegistry:
        ps=tuple(sorted(profiles,key=lambda p:p.canonical_market_id))
        if any(not isinstance(p,MarketDependencyProfile) for p in ps):
            raise TypeError("profiles must contain MarketDependencyProfile")
        if not isinstance(constraint_graph,MarketConstraintGraph):
            raise TypeError("constraint_graph must be MarketConstraintGraph")

        dependency={}
        role={}
        constraint={}

        for p in ps:
            for d in p.dependencies:
                dependency.setdefault(d.kind+"="+d.key,[]).append(p.canonical_market_id)
                role.setdefault(d.role,[]).append(p.canonical_market_id)

        for c in constraint_graph.constraints:
            bucket=constraint.setdefault(c.constraint_type,[])
            bucket.extend((c.source_market_id,c.target_market_id))

        for index in (dependency,role,constraint):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        return DependencyRegistry(
            ps,
            constraint_graph.graph_hash,
            dependency,
            role,
            constraint,
            lineage,
        )

def build_umd_114_certification_manifest():
    data={
        "subsystem_id":"UMD",
        "build_id":UMD_114_BUILD_ID,
        "revision":UMD_114_REVISION,
        "schema_version":UMD_114_SCHEMA_VERSION,
        "upstream_builds":("UMD-112","UMD-113"),
        "mode":"deterministic_read_only_dependency_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,
        "persistence_enabled":False,
        "mutation_enabled":False,
        "publication_enabled":False,
        "execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_114_dependency_registry()->bool:
    if verify_umd_113_market_constraint_graph() is not True:
        return False
    m=build_umd_114_certification_manifest()
    return m["build_id"]=="UMD-114" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
