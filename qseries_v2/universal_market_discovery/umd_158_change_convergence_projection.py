from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_153_change_dependency_context_registry import ChangeDependencyContextRegistry
from .umd_157_change_co_occurrence_model import ChangeCoOccurrenceModel,ChangeCoOccurrence,verify_umd_157_change_co_occurrence_model

UMD_158_BUILD_ID="UMD-158"
UMD_158_REVISION="UMD_158_CHANGE_CONVERGENCE_PROJECTION_V1"
UMD_158_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ChangeConvergence:
    canonical_market_id:str
    change_hashes:Tuple[str,...]
    relation_types:Tuple[str,...]
    dependency_keys:Tuple[str,...]
    dependency_roles:Tuple[str,...]
    constraint_types:Tuple[str,...]
    boundary_change_hashes:Tuple[str,...]
    occurrence_hash:str

    def __post_init__(self):
        for name in (
            "change_hashes","relation_types","dependency_keys",
            "dependency_roles","constraint_types","boundary_change_hashes"
        ):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        if len(self.change_hashes)<2:
            raise ValueError("convergence requires at least two distinct changes")
        if not self.canonical_market_id:
            raise ValueError("canonical_market_id must be non-empty")

    @property
    def convergence_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "change_hashes":self.change_hashes,
            "relation_types":self.relation_types,
            "dependency_keys":self.dependency_keys,
            "dependency_roles":self.dependency_roles,
            "constraint_types":self.constraint_types,
            "boundary_change_hashes":self.boundary_change_hashes,
            "occurrence_hash":self.occurrence_hash,
        })

@dataclass(frozen=True,slots=True)
class ChangeConvergenceProjection:
    convergences:Tuple[ChangeConvergence,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"convergences",tuple(self.convergences))
        if self.convergences!=tuple(sorted(
            self.convergences,key=lambda c:(c.canonical_market_id,c.convergence_hash)
        )):
            raise ValueError("convergences must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_158_BUILD_ID:
            raise ValueError("lineage must belong to UMD-158")
        required={c.convergence_hash for c in self.convergences}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every convergence hash")

    @property
    def projection_hash(self)->str:
        return deterministic_sha256({
            "convergence_hashes":tuple(c.convergence_hash for c in self.convergences),
            "lineage":self.lineage,
        })

class ChangeConvergenceProjector:
    __slots__=()

    def project(
        self,
        co_occurrence_model:ChangeCoOccurrenceModel,
        dependency_context:ChangeDependencyContextRegistry,
        *,
        lineage_factory,
    )->ChangeConvergenceProjection:
        if not isinstance(co_occurrence_model,ChangeCoOccurrenceModel):
            raise TypeError("co_occurrence_model must be ChangeCoOccurrenceModel")
        if not isinstance(dependency_context,ChangeDependencyContextRegistry):
            raise TypeError("dependency_context must be ChangeDependencyContextRegistry")

        convergences=[]

        for occurrence in co_occurrence_model.occurrences:
            market_id=occurrence.canonical_market_id
            change_set=set(occurrence.change_hashes)

            dependency_keys=tuple(sorted(
                key for key,changes in dependency_context.dependency_index.items()
                if change_set.intersection(changes)
            ))
            dependency_roles=tuple(sorted(
                role for role,changes in dependency_context.role_index.items()
                if change_set.intersection(changes)
            ))
            constraint_types=tuple(sorted(
                ctype for ctype,changes in dependency_context.constraint_type_index.items()
                if change_set.intersection(changes)
            ))
            boundary_changes=tuple(sorted(
                change_set.intersection(
                    dependency_context.boundary_market_index.get(market_id,())
                )
            ))

            convergences.append(ChangeConvergence(
                market_id,
                occurrence.change_hashes,
                tuple(sorted(occurrence.relation_types)),
                dependency_keys,
                dependency_roles,
                constraint_types,
                boundary_changes,
                occurrence.occurrence_hash,
            ))

        convergences.sort(key=lambda c:(c.canonical_market_id,c.convergence_hash))
        lineage=lineage_factory(tuple(c.convergence_hash for c in convergences))
        return ChangeConvergenceProjection(tuple(convergences),lineage)

def build_umd_158_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_158_BUILD_ID,"revision":UMD_158_REVISION,
        "schema_version":UMD_158_SCHEMA_VERSION,"upstream_builds":("UMD-153","UMD-157"),
        "mode":"deterministic_read_only_change_convergence_projection",
        "semantics":"context_enrichment_only_no_convergence_score",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_158_change_convergence_projection()->bool:
    if verify_umd_157_change_co_occurrence_model() is not True:
        return False
    m=build_umd_158_certification_manifest()
    return m["build_id"]=="UMD-158" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
