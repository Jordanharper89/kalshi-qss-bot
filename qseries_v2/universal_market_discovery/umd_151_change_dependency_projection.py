from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_112_market_dependency import MarketDependency
from .umd_114_dependency_registry import DependencyRegistry
from .umd_150_change_structure_registry import ChangeStructureRegistry,verify_umd_150_change_structure_registry

UMD_151_BUILD_ID="UMD-151"
UMD_151_REVISION="UMD_151_CHANGE_DEPENDENCY_PROJECTION_V1"
UMD_151_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ChangeDependencyBinding:
    canonical_market_id:str
    kind:str
    key:str
    role:str
    dependency_hash:str

    @property
    def binding_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "kind":self.kind,
            "key":self.key,
            "role":self.role,
            "dependency_hash":self.dependency_hash,
        })

@dataclass(frozen=True,slots=True)
class ChangeDependencyProjection:
    change_hash:str
    market_ids:Tuple[str,...]
    bindings:Tuple[ChangeDependencyBinding,...]
    role_to_markets:Mapping[str,Tuple[str,...]]
    dependency_to_markets:Mapping[str,Tuple[str,...]]
    missing_profile_market_ids:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"market_ids",tuple(self.market_ids))
        object.__setattr__(self,"bindings",tuple(self.bindings))
        object.__setattr__(self,"role_to_markets",_freeze(self.role_to_markets))
        object.__setattr__(self,"dependency_to_markets",_freeze(self.dependency_to_markets))
        object.__setattr__(self,"missing_profile_market_ids",tuple(self.missing_profile_market_ids))
        if self.market_ids!=tuple(sorted(set(self.market_ids))):
            raise ValueError("market_ids must be unique and sorted")
        if self.bindings!=tuple(sorted(
            self.bindings,
            key=lambda b:(b.canonical_market_id,b.kind,b.key,b.role,b.dependency_hash)
        )):
            raise ValueError("bindings must be deterministically sorted")
        if self.missing_profile_market_ids!=tuple(sorted(set(self.missing_profile_market_ids))):
            raise ValueError("missing_profile_market_ids must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_151_BUILD_ID:
            raise ValueError("lineage must belong to UMD-151")
        if self.change_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include change hash")

    def markets_for_role(self,role:str)->Tuple[str,...]:
        return self.role_to_markets.get(role,())

    def markets_for_dependency(self,kind:str,key:str)->Tuple[str,...]:
        return self.dependency_to_markets.get(kind+"="+key,())

    @property
    def projection_hash(self)->str:
        return deterministic_sha256({
            "change_hash":self.change_hash,
            "market_ids":self.market_ids,
            "binding_hashes":tuple(b.binding_hash for b in self.bindings),
            "role_to_markets":self.role_to_markets,
            "dependency_to_markets":self.dependency_to_markets,
            "missing_profile_market_ids":self.missing_profile_market_ids,
            "lineage":self.lineage,
        })

class ChangeDependencyProjector:
    __slots__=("structure_registry","dependency_registry")

    def __init__(self,structure_registry:ChangeStructureRegistry,dependency_registry:DependencyRegistry):
        if not isinstance(structure_registry,ChangeStructureRegistry):
            raise TypeError("structure_registry must be ChangeStructureRegistry")
        if not isinstance(dependency_registry,DependencyRegistry):
            raise TypeError("dependency_registry must be DependencyRegistry")
        self.structure_registry=structure_registry
        self.dependency_registry=dependency_registry

    def project(self,change_hash:str,*,lineage:ImmutableLineage)->ChangeDependencyProjection:
        markets=tuple(sorted(
            market_id for market_id,changes in self.structure_registry.market_index.items()
            if change_hash in changes
        ))
        profiles={p.canonical_market_id:p for p in self.dependency_registry.profiles}

        bindings=[]
        role_index={}
        dependency_index={}
        missing=[]

        for market_id in markets:
            profile=profiles.get(market_id)
            if profile is None:
                missing.append(market_id)
                continue
            for dependency in profile.dependencies:
                binding=ChangeDependencyBinding(
                    market_id,
                    dependency.kind,
                    dependency.key,
                    dependency.role,
                    dependency.dependency_hash,
                )
                bindings.append(binding)
                role_index.setdefault(dependency.role,[]).append(market_id)
                dependency_index.setdefault(dependency.kind+"="+dependency.key,[]).append(market_id)

        bindings.sort(key=lambda b:(b.canonical_market_id,b.kind,b.key,b.role,b.dependency_hash))
        for index in (role_index,dependency_index):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        return ChangeDependencyProjection(
            change_hash,
            markets,
            tuple(bindings),
            role_index,
            dependency_index,
            tuple(sorted(missing)),
            lineage,
        )

def build_umd_151_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_151_BUILD_ID,"revision":UMD_151_REVISION,
        "schema_version":UMD_151_SCHEMA_VERSION,"upstream_builds":("UMD-112","UMD-114","UMD-150"),
        "mode":"deterministic_read_only_change_dependency_projection",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_151_change_dependency_projection()->bool:
    if verify_umd_150_change_structure_registry() is not True:
        return False
    m=build_umd_151_certification_manifest()
    return m["build_id"]=="UMD-151" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
