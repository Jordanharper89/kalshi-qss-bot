from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_109_market_semantic_profile import semantic_key
from .umd_114_dependency_registry import DependencyRegistry, verify_umd_114_dependency_registry

UMD_115_BUILD_ID="UMD-115"
UMD_115_REVISION="UMD_115_OBSERVATION_IMPACT_MAPPING_V1"
UMD_115_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
OBSERVATION_FIELDS=("entity","asset","event","metric","geography","time_window","settlement_source","external_state")

@dataclass(frozen=True,slots=True)
class ObservationDescriptor:
    observation_id:str
    facts:Tuple[Tuple[str,str],...]
    lineage:ImmutableLineage

    def __post_init__(self):
        if not isinstance(self.observation_id,str) or not self.observation_id:
            raise ValueError("observation_id must be non-empty")
        normalized=[]
        for kind,key in self.facts:
            if kind not in OBSERVATION_FIELDS:
                raise ValueError("unsupported observation fact kind")
            normalized.append((kind,semantic_key(key)))
        normalized=tuple(sorted(set(normalized)))
        object.__setattr__(self,"facts",normalized)
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_115_BUILD_ID:
            raise ValueError("lineage must belong to UMD-115")

    @property
    def observation_hash(self)->str:
        return deterministic_sha256({
            "observation_id":self.observation_id,
            "facts":self.facts,
            "lineage":self.lineage,
        })

@dataclass(frozen=True,slots=True)
class DirectImpactResult:
    observation_hash:str
    market_ids:Tuple[str,...]
    matched_dependencies:Tuple[Tuple[str,str,Tuple[str,...]],...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"market_ids",tuple(self.market_ids))
        object.__setattr__(self,"matched_dependencies",tuple(self.matched_dependencies))
        if tuple(sorted(set(self.market_ids)))!=self.market_ids:
            raise ValueError("market_ids must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_115_BUILD_ID:
            raise ValueError("lineage must belong to UMD-115")
        if self.observation_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include observation hash")

    @property
    def impact_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "market_ids":self.market_ids,
            "matched_dependencies":self.matched_dependencies,
            "lineage":self.lineage,
        })

class ObservationImpactMapper:
    __slots__=("registry",)

    def __init__(self,registry:DependencyRegistry):
        if not isinstance(registry,DependencyRegistry):
            raise TypeError("registry must be DependencyRegistry")
        self.registry=registry

    def map(self,observation:ObservationDescriptor,*,lineage:ImmutableLineage)->DirectImpactResult:
        if not isinstance(observation,ObservationDescriptor):
            raise TypeError("observation must be ObservationDescriptor")
        markets=set()
        matched=[]
        for kind,key in observation.facts:
            ids=self.registry.markets_for_dependency(kind,key)
            if ids:
                markets.update(ids)
                matched.append((kind,key,ids))
        return DirectImpactResult(
            observation.observation_hash,
            tuple(sorted(markets)),
            tuple(sorted(matched)),
            lineage,
        )

def build_umd_115_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_115_BUILD_ID,"revision":UMD_115_REVISION,
        "schema_version":UMD_115_SCHEMA_VERSION,"upstream_builds":("UMD-109","UMD-114"),
        "mode":"deterministic_read_only_observation_impact_mapping",
        "observation_fields":OBSERVATION_FIELDS,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_115_observation_impact_mapping()->bool:
    if verify_umd_114_dependency_registry() is not True:
        return False
    m=build_umd_115_certification_manifest()
    return m["build_id"]=="UMD-115" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
