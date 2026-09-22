from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_159_change_convergence_registry import ChangeConvergenceRegistry
from .umd_162_convergence_change_registry import ConvergenceChangeRegistry,verify_umd_162_convergence_change_registry

UMD_166_BUILD_ID="UMD-166"
UMD_166_REVISION="UMD_166_CONVERGENCE_DEPENDENCY_PROJECTION_V1"
UMD_166_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ConvergenceDependencyContext:
    canonical_market_id:str
    convergence_change_types:Tuple[str,...]
    dependency_keys:Tuple[str,...]
    dependency_roles:Tuple[str,...]

    def __post_init__(self):
        for name in ("convergence_change_types","dependency_keys","dependency_roles"):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        if not self.canonical_market_id:
            raise ValueError("canonical_market_id must be non-empty")
        if not self.convergence_change_types:
            raise ValueError("convergence change context requires at least one change type")

    @property
    def context_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "convergence_change_types":self.convergence_change_types,
            "dependency_keys":self.dependency_keys,
            "dependency_roles":self.dependency_roles,
        })

@dataclass(frozen=True,slots=True)
class ConvergenceDependencyProjection:
    contexts:Tuple[ConvergenceDependencyContext,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"contexts",tuple(self.contexts))
        if self.contexts!=tuple(sorted(
            self.contexts,key=lambda c:(c.canonical_market_id,c.context_hash)
        )):
            raise ValueError("contexts must be deterministically sorted")
        if len({c.canonical_market_id for c in self.contexts})!=len(self.contexts):
            raise ValueError("market dependency contexts must be unique")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_166_BUILD_ID:
            raise ValueError("lineage must belong to UMD-166")
        required={c.context_hash for c in self.contexts}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every dependency context hash")

    def context_for_market(self,market_id:str)->ConvergenceDependencyContext|None:
        for context in self.contexts:
            if context.canonical_market_id==market_id:
                return context
        return None

    @property
    def projection_hash(self)->str:
        return deterministic_sha256({
            "context_hashes":tuple(c.context_hash for c in self.contexts),
            "lineage":self.lineage,
        })

class ConvergenceDependencyProjector:
    __slots__=("convergence_registry","change_registry")

    def __init__(
        self,
        convergence_registry:ChangeConvergenceRegistry,
        change_registry:ConvergenceChangeRegistry,
    ):
        if not isinstance(convergence_registry,ChangeConvergenceRegistry):
            raise TypeError("convergence_registry must be ChangeConvergenceRegistry")
        if not isinstance(change_registry,ConvergenceChangeRegistry):
            raise TypeError("change_registry must be ConvergenceChangeRegistry")
        self.convergence_registry=convergence_registry
        self.change_registry=change_registry

    def project(self,*,lineage_factory)->ConvergenceDependencyProjection:
        market_types={}
        for record in self.change_registry.records:
            market_types.setdefault(record.canonical_market_id,[]).append(record.change_type)

        contexts=[]
        for market_id,types in sorted(market_types.items()):
            dependencies=tuple(sorted(
                key for key,markets in self.convergence_registry.dependency_index.items()
                if market_id in markets
            ))
            roles=tuple(sorted(
                role for role,markets in self.convergence_registry.role_index.items()
                if market_id in markets
            ))
            contexts.append(ConvergenceDependencyContext(
                market_id,
                tuple(sorted(set(types))),
                dependencies,
                roles,
            ))

        contexts.sort(key=lambda c:(c.canonical_market_id,c.context_hash))
        lineage=lineage_factory(tuple(c.context_hash for c in contexts))
        return ConvergenceDependencyProjection(tuple(contexts),lineage)

def build_umd_166_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_166_BUILD_ID,"revision":UMD_166_REVISION,
        "schema_version":UMD_166_SCHEMA_VERSION,"upstream_builds":("UMD-159","UMD-162"),
        "mode":"deterministic_read_only_convergence_dependency_projection",
        "semantics":"dependency_context_only_no_score_or_prediction",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_166_convergence_dependency_projection()->bool:
    if verify_umd_162_convergence_change_registry() is not True:
        return False
    m=build_umd_166_certification_manifest()
    return m["build_id"]=="UMD-166" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
