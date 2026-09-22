from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_159_change_convergence_registry import ChangeConvergenceRegistry
from .umd_166_convergence_dependency_projection import ConvergenceDependencyProjection,verify_umd_166_convergence_dependency_projection

UMD_167_BUILD_ID="UMD-167"
UMD_167_REVISION="UMD_167_CONVERGENCE_CONSTRAINT_PROJECTION_V1"
UMD_167_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ConvergenceConstraintContext:
    canonical_market_id:str
    convergence_change_types:Tuple[str,...]
    constraint_types:Tuple[str,...]
    relation_types:Tuple[str,...]

    def __post_init__(self):
        for name in ("convergence_change_types","constraint_types","relation_types"):
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
            "constraint_types":self.constraint_types,
            "relation_types":self.relation_types,
        })

@dataclass(frozen=True,slots=True)
class ConvergenceConstraintProjection:
    contexts:Tuple[ConvergenceConstraintContext,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"contexts",tuple(self.contexts))
        if self.contexts!=tuple(sorted(
            self.contexts,key=lambda c:(c.canonical_market_id,c.context_hash)
        )):
            raise ValueError("contexts must be deterministically sorted")
        if len({c.canonical_market_id for c in self.contexts})!=len(self.contexts):
            raise ValueError("market constraint contexts must be unique")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_167_BUILD_ID:
            raise ValueError("lineage must belong to UMD-167")
        required={c.context_hash for c in self.contexts}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every constraint context hash")

    def context_for_market(self,market_id:str)->ConvergenceConstraintContext|None:
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

class ConvergenceConstraintProjector:
    __slots__=("convergence_registry",)

    def __init__(self,convergence_registry:ChangeConvergenceRegistry):
        if not isinstance(convergence_registry,ChangeConvergenceRegistry):
            raise TypeError("convergence_registry must be ChangeConvergenceRegistry")
        self.convergence_registry=convergence_registry

    def project(
        self,
        dependency_projection:ConvergenceDependencyProjection,
        *,
        lineage_factory,
    )->ConvergenceConstraintProjection:
        if not isinstance(dependency_projection,ConvergenceDependencyProjection):
            raise TypeError("dependency_projection must be ConvergenceDependencyProjection")

        contexts=[]
        for dependency_context in dependency_projection.contexts:
            market_id=dependency_context.canonical_market_id
            constraints=tuple(sorted(
                ctype for ctype,markets in self.convergence_registry.constraint_type_index.items()
                if market_id in markets
            ))
            relations=tuple(sorted(
                relation for relation,markets in self.convergence_registry.relation_index.items()
                if market_id in markets
            ))
            contexts.append(ConvergenceConstraintContext(
                market_id,
                dependency_context.convergence_change_types,
                constraints,
                relations,
            ))

        contexts.sort(key=lambda c:(c.canonical_market_id,c.context_hash))
        lineage=lineage_factory(tuple(c.context_hash for c in contexts))
        return ConvergenceConstraintProjection(tuple(contexts),lineage)

def build_umd_167_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_167_BUILD_ID,"revision":UMD_167_REVISION,
        "schema_version":UMD_167_SCHEMA_VERSION,"upstream_builds":("UMD-159","UMD-166"),
        "mode":"deterministic_read_only_convergence_constraint_projection",
        "semantics":"constraint_and_relation_context_only_no_score_or_prediction",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_167_convergence_constraint_projection()->bool:
    if verify_umd_166_convergence_dependency_projection() is not True:
        return False
    m=build_umd_167_certification_manifest()
    return m["build_id"]=="UMD-167" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
