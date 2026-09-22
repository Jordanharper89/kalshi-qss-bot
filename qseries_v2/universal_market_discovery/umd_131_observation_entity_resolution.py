from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_109_market_semantic_profile import semantic_key
from .umd_111_semantic_registry import SemanticRegistry
from .umd_112_market_dependency import DEPENDENCY_KINDS
from .umd_114_dependency_registry import DependencyRegistry
from .umd_130_observation_classification import CanonicalObservationClassification,verify_umd_130_observation_classification

UMD_131_BUILD_ID="UMD-131"
UMD_131_REVISION="UMD_131_OBSERVATION_ENTITY_RESOLUTION_V1"
UMD_131_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
RESOLVABLE_ENTITY_KINDS=tuple(
    kind for kind in DEPENDENCY_KINDS
    if kind not in ("time_window","external_state")
)

@dataclass(frozen=True,slots=True)
class ObservationEntityBinding:
    kind:str
    source_value:str
    canonical_key:str
    known_market_ids:Tuple[str,...]

    def __post_init__(self):
        if self.kind not in RESOLVABLE_ENTITY_KINDS:
            raise ValueError("unsupported resolvable entity kind")
        if self.canonical_key!=semantic_key(self.source_value):
            raise ValueError("canonical_key does not match source_value")
        object.__setattr__(self,"known_market_ids",tuple(self.known_market_ids))
        if self.known_market_ids!=tuple(sorted(set(self.known_market_ids))):
            raise ValueError("known_market_ids must be unique and sorted")
        if not self.known_market_ids:
            raise ValueError("resolved entity binding requires at least one known market")

    @property
    def binding_hash(self)->str:
        return deterministic_sha256({
            "kind":self.kind,
            "canonical_key":self.canonical_key,
            "known_market_ids":self.known_market_ids,
        })

@dataclass(frozen=True,slots=True)
class ObservationEntityResolution:
    observation_id:str
    classification_hash:str
    bindings:Tuple[ObservationEntityBinding,...]
    unresolved:Tuple[Tuple[str,str],...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"bindings",tuple(self.bindings))
        object.__setattr__(self,"unresolved",tuple(self.unresolved))
        if self.bindings!=tuple(sorted(self.bindings,key=lambda b:(b.kind,b.canonical_key,b.binding_hash))):
            raise ValueError("bindings must be deterministically sorted")
        if self.unresolved!=tuple(sorted(set(self.unresolved))):
            raise ValueError("unresolved entries must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_131_BUILD_ID:
            raise ValueError("lineage must belong to UMD-131")
        if self.classification_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include classification hash")

    @property
    def resolution_hash(self)->str:
        return deterministic_sha256({
            "observation_id":self.observation_id,
            "classification_hash":self.classification_hash,
            "binding_hashes":tuple(b.binding_hash for b in self.bindings),
            "unresolved":self.unresolved,
            "lineage":self.lineage,
        })

class ObservationEntityResolver:
    __slots__=("semantic_registry","dependency_registry")

    def __init__(
        self,
        semantic_registry:SemanticRegistry,
        dependency_registry:DependencyRegistry,
    ):
        if not isinstance(semantic_registry,SemanticRegistry):
            raise TypeError("semantic_registry must be SemanticRegistry")
        if not isinstance(dependency_registry,DependencyRegistry):
            raise TypeError("dependency_registry must be DependencyRegistry")
        self.semantic_registry=semantic_registry
        self.dependency_registry=dependency_registry

    def resolve(
        self,
        classification:CanonicalObservationClassification,
        candidates:Iterable[tuple[str,str]],
        *,
        lineage:ImmutableLineage,
    )->ObservationEntityResolution:
        if not isinstance(classification,CanonicalObservationClassification):
            raise TypeError("classification must be CanonicalObservationClassification")

        bindings=[]
        unresolved=[]
        seen=set()

        for kind,value in candidates:
            if kind not in RESOLVABLE_ENTITY_KINDS:
                raise ValueError("unsupported resolvable entity kind")
            key=semantic_key(value)
            identity=(kind,key)
            if identity in seen:
                continue
            seen.add(identity)

            markets=set(self.semantic_registry.markets_with(kind,key))
            markets.update(self.dependency_registry.markets_for_dependency(kind,key))

            if markets:
                bindings.append(ObservationEntityBinding(
                    kind,
                    value,
                    key,
                    tuple(sorted(markets)),
                ))
            else:
                unresolved.append((kind,key))

        bindings.sort(key=lambda b:(b.kind,b.canonical_key,b.binding_hash))
        unresolved=tuple(sorted(set(unresolved)))

        return ObservationEntityResolution(
            classification.observation_id,
            classification.classification_hash,
            tuple(bindings),
            unresolved,
            lineage,
        )

def build_umd_131_certification_manifest():
    data={
        "subsystem_id":"UMD",
        "build_id":UMD_131_BUILD_ID,
        "revision":UMD_131_REVISION,
        "schema_version":UMD_131_SCHEMA_VERSION,
        "upstream_builds":("UMD-111","UMD-114","UMD-130"),
        "mode":"deterministic_read_only_observation_entity_resolution",
        "resolvable_entity_kinds":RESOLVABLE_ENTITY_KINDS,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,
        "persistence_enabled":False,
        "mutation_enabled":False,
        "publication_enabled":False,
        "execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_131_observation_entity_resolution()->bool:
    if verify_umd_130_observation_classification() is not True:
        return False
    m=build_umd_131_certification_manifest()
    return m["build_id"]=="UMD-131" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
