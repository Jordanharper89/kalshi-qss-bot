from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_165_convergence_surface_registry import ConvergenceSurfaceRegistry
from .umd_168_convergence_context_registry import ConvergenceContextRegistry,verify_umd_168_convergence_context_registry

UMD_169_BUILD_ID="UMD-169"
UMD_169_REVISION="UMD_169_CONVERGENCE_MARKET_PROFILE_V1"
UMD_169_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ConvergenceMarketProfile:
    canonical_market_id:str
    change_types:Tuple[str,...]
    ladder_hashes:Tuple[str,...]
    partition_hashes:Tuple[str,...]
    venue_keys:Tuple[str,...]
    dependency_keys:Tuple[str,...]
    dependency_roles:Tuple[str,...]
    constraint_types:Tuple[str,...]
    relation_types:Tuple[str,...]

    def __post_init__(self):
        if not self.canonical_market_id:
            raise ValueError("canonical_market_id must be non-empty")
        for name in (
            "change_types","ladder_hashes","partition_hashes","venue_keys",
            "dependency_keys","dependency_roles","constraint_types","relation_types"
        ):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        if not self.change_types:
            raise ValueError("profile requires at least one convergence change type")

    @property
    def profile_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "change_types":self.change_types,
            "ladder_hashes":self.ladder_hashes,
            "partition_hashes":self.partition_hashes,
            "venue_keys":self.venue_keys,
            "dependency_keys":self.dependency_keys,
            "dependency_roles":self.dependency_roles,
            "constraint_types":self.constraint_types,
            "relation_types":self.relation_types,
        })

@dataclass(frozen=True,slots=True)
class ConvergenceMarketProfileSet:
    profiles:Tuple[ConvergenceMarketProfile,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"profiles",tuple(self.profiles))
        if self.profiles!=tuple(sorted(self.profiles,key=lambda p:(p.canonical_market_id,p.profile_hash))):
            raise ValueError("profiles must be deterministically sorted")
        if len({p.canonical_market_id for p in self.profiles})!=len(self.profiles):
            raise ValueError("canonical market profiles must be unique")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_169_BUILD_ID:
            raise ValueError("lineage must belong to UMD-169")
        required={p.profile_hash for p in self.profiles}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every market profile hash")

    def get(self,market_id:str)->ConvergenceMarketProfile|None:
        for profile in self.profiles:
            if profile.canonical_market_id==market_id:
                return profile
        return None

    @property
    def profile_set_hash(self)->str:
        return deterministic_sha256({
            "profile_hashes":tuple(p.profile_hash for p in self.profiles),
            "lineage":self.lineage,
        })

class ConvergenceMarketProfiler:
    __slots__=("surface_registry","context_registry")

    def __init__(
        self,
        surface_registry:ConvergenceSurfaceRegistry,
        context_registry:ConvergenceContextRegistry,
    ):
        if not isinstance(surface_registry,ConvergenceSurfaceRegistry):
            raise TypeError("surface_registry must be ConvergenceSurfaceRegistry")
        if not isinstance(context_registry,ConvergenceContextRegistry):
            raise TypeError("context_registry must be ConvergenceContextRegistry")
        self.surface_registry=surface_registry
        self.context_registry=context_registry

    @staticmethod
    def _reverse(index,market_id):
        return tuple(sorted(key for key,markets in index.items() if market_id in markets))

    def build(self,*,lineage_factory)->ConvergenceMarketProfileSet:
        surface_markets=set(self.surface_registry.market_index)
        context_markets=set(self.context_registry.market_index)
        markets=tuple(sorted(surface_markets|context_markets))
        profiles=[]

        for market_id in markets:
            surface_types=self.surface_registry.change_types_for_market(market_id)
            context_types=self.context_registry.change_types_for_market(market_id)
            if surface_types and context_types and surface_types!=context_types:
                raise ValueError("surface/context convergence change types disagree")
            change_types=surface_types or context_types

            profiles.append(ConvergenceMarketProfile(
                market_id,
                change_types,
                self._reverse(self.surface_registry.ladder_index,market_id),
                self._reverse(self.surface_registry.partition_index,market_id),
                self._reverse(self.surface_registry.venue_index,market_id),
                self._reverse(self.context_registry.dependency_index,market_id),
                self._reverse(self.context_registry.role_index,market_id),
                self._reverse(self.context_registry.constraint_index,market_id),
                self._reverse(self.context_registry.relation_index,market_id),
            ))

        profiles.sort(key=lambda p:(p.canonical_market_id,p.profile_hash))
        lineage=lineage_factory(tuple(p.profile_hash for p in profiles))
        return ConvergenceMarketProfileSet(tuple(profiles),lineage)

def build_umd_169_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_169_BUILD_ID,"revision":UMD_169_REVISION,
        "schema_version":UMD_169_SCHEMA_VERSION,"upstream_builds":("UMD-165","UMD-168"),
        "mode":"deterministic_read_only_convergence_market_profile",
        "semantics":"canonical_structural_profile_no_score_probability_or_prediction",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_169_convergence_market_profile()->bool:
    if verify_umd_168_convergence_context_registry() is not True:
        return False
    m=build_umd_169_certification_manifest()
    return m["build_id"]=="UMD-169" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
