from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_169_convergence_market_profile import ConvergenceMarketProfile,ConvergenceMarketProfileSet,verify_umd_169_convergence_market_profile

UMD_170_BUILD_ID="UMD-170"
UMD_170_REVISION="UMD_170_CONVERGENCE_MARKET_REGISTRY_V1"
UMD_170_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ConvergenceMarketRegistry:
    profiles:Tuple[ConvergenceMarketProfile,...]
    change_type_index:Mapping[str,Tuple[str,...]]
    ladder_index:Mapping[str,Tuple[str,...]]
    partition_index:Mapping[str,Tuple[str,...]]
    venue_index:Mapping[str,Tuple[str,...]]
    dependency_index:Mapping[str,Tuple[str,...]]
    role_index:Mapping[str,Tuple[str,...]]
    constraint_index:Mapping[str,Tuple[str,...]]
    relation_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"profiles",tuple(self.profiles))
        for name in (
            "change_type_index","ladder_index","partition_index","venue_index",
            "dependency_index","role_index","constraint_index","relation_index"
        ):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.profiles!=tuple(sorted(self.profiles,key=lambda p:(p.canonical_market_id,p.profile_hash))):
            raise ValueError("profiles must be deterministically sorted")
        if len({p.canonical_market_id for p in self.profiles})!=len(self.profiles):
            raise ValueError("registry profiles must have unique market ids")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_170_BUILD_ID:
            raise ValueError("lineage must belong to UMD-170")
        required={p.profile_hash for p in self.profiles}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every market profile hash")

    def get(self,market_id:str)->ConvergenceMarketProfile|None:
        for profile in self.profiles:
            if profile.canonical_market_id==market_id:
                return profile
        return None

    def markets_for_change_type(self,key:str)->Tuple[str,...]: return self.change_type_index.get(key,())
    def markets_for_ladder(self,key:str)->Tuple[str,...]: return self.ladder_index.get(key,())
    def markets_for_partition(self,key:str)->Tuple[str,...]: return self.partition_index.get(key,())
    def markets_for_venue(self,key:str)->Tuple[str,...]: return self.venue_index.get(key,())
    def markets_for_dependency(self,key:str)->Tuple[str,...]: return self.dependency_index.get(key,())
    def markets_for_role(self,key:str)->Tuple[str,...]: return self.role_index.get(key,())
    def markets_for_constraint(self,key:str)->Tuple[str,...]: return self.constraint_index.get(key,())
    def markets_for_relation(self,key:str)->Tuple[str,...]: return self.relation_index.get(key,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "profile_hashes":tuple(p.profile_hash for p in self.profiles),
            "change_type_index":self.change_type_index,
            "ladder_index":self.ladder_index,
            "partition_index":self.partition_index,
            "venue_index":self.venue_index,
            "dependency_index":self.dependency_index,
            "role_index":self.role_index,
            "constraint_index":self.constraint_index,
            "relation_index":self.relation_index,
            "lineage":self.lineage,
        })

class ConvergenceMarketRegistryBuilder:
    __slots__=()

    def build(self,profile_set:ConvergenceMarketProfileSet,*,lineage_factory)->ConvergenceMarketRegistry:
        if not isinstance(profile_set,ConvergenceMarketProfileSet):
            raise TypeError("profile_set must be ConvergenceMarketProfileSet")

        indexes=[{} for _ in range(8)]
        attrs=(
            "change_types","ladder_hashes","partition_hashes","venue_keys",
            "dependency_keys","dependency_roles","constraint_types","relation_types"
        )
        for profile in profile_set.profiles:
            for index,attr in zip(indexes,attrs):
                for key in getattr(profile,attr):
                    index.setdefault(key,[]).append(profile.canonical_market_id)

        for index in indexes:
            for key,items in index.items():
                index[key]=tuple(sorted(set(items)))

        lineage=lineage_factory(tuple(p.profile_hash for p in profile_set.profiles))
        return ConvergenceMarketRegistry(profile_set.profiles,*indexes,lineage)

def build_umd_170_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_170_BUILD_ID,"revision":UMD_170_REVISION,
        "schema_version":UMD_170_SCHEMA_VERSION,"upstream_builds":("UMD-169",),
        "mode":"deterministic_read_only_convergence_market_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_170_convergence_market_registry()->bool:
    if verify_umd_169_convergence_market_profile() is not True:
        return False
    m=build_umd_170_certification_manifest()
    return m["build_id"]=="UMD-170" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
