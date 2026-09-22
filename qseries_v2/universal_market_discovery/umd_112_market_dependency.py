from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_109_market_semantic_profile import MarketSemanticProfile, semantic_key
from .umd_111_semantic_registry import verify_umd_111_semantic_registry

UMD_112_BUILD_ID="UMD-112"
UMD_112_REVISION="UMD_112_MARKET_DEPENDENCY_MODEL_V1"
UMD_112_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
DEPENDENCY_ROLES=("required","supporting","settlement","context")
DEPENDENCY_KINDS=("entity","asset","event","metric","geography","time_window","settlement_source","external_state")

@dataclass(frozen=True,slots=True)
class MarketDependency:
    kind:str
    value:str
    key:str
    role:str

    def __post_init__(self):
        if self.kind not in DEPENDENCY_KINDS:
            raise ValueError("unsupported dependency kind")
        if self.role not in DEPENDENCY_ROLES:
            raise ValueError("unsupported dependency role")
        if self.key!=semantic_key(self.value):
            raise ValueError("dependency key does not match value")

    @property
    def dependency_hash(self)->str:
        return deterministic_sha256({
            "kind":self.kind,
            "key":self.key,
            "role":self.role,
        })

@dataclass(frozen=True,slots=True)
class MarketDependencyProfile:
    canonical_market_id:str
    semantic_profile_hash:str
    dependencies:Tuple[MarketDependency,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"dependencies",tuple(self.dependencies))
        expected=tuple(sorted(self.dependencies,key=lambda d:(d.kind,d.key,d.role)))
        if expected!=self.dependencies:
            raise ValueError("dependencies must be deterministically sorted")
        keys=[(d.kind,d.key,d.role) for d in self.dependencies]
        if len(keys)!=len(set(keys)):
            raise ValueError("duplicate market dependency")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_112_BUILD_ID:
            raise ValueError("lineage must belong to UMD-112")
        if self.semantic_profile_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include semantic profile hash")

    def dependency_keys(self,kind:str|None=None,role:str|None=None)->Tuple[str,...]:
        return tuple(
            d.key for d in self.dependencies
            if (kind is None or d.kind==kind) and (role is None or d.role==role)
        )

    @property
    def profile_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "semantic_profile_hash":self.semantic_profile_hash,
            "dependencies":tuple({
                "kind":d.kind,
                "key":d.key,
                "role":d.role,
            } for d in self.dependencies),
            "lineage":self.lineage,
        })

class MarketDependencyBuilder:
    __slots__=()

    def build(
        self,
        profile:MarketSemanticProfile,
        dependencies:Iterable[tuple[str,str,str]],
        *,
        lineage:ImmutableLineage,
    )->MarketDependencyProfile:
        if not isinstance(profile,MarketSemanticProfile):
            raise TypeError("profile must be MarketSemanticProfile")
        built=[]
        seen=set()
        for kind,value,role in dependencies:
            key=semantic_key(value)
            identity=(kind,key,role)
            if identity in seen:
                continue
            seen.add(identity)
            built.append(MarketDependency(kind,value,key,role))
        built.sort(key=lambda d:(d.kind,d.key,d.role))
        return MarketDependencyProfile(
            profile.canonical_market_id,
            profile.profile_hash,
            tuple(built),
            lineage,
        )

def build_umd_112_certification_manifest():
    data={
        "subsystem_id":"UMD",
        "build_id":UMD_112_BUILD_ID,
        "revision":UMD_112_REVISION,
        "schema_version":UMD_112_SCHEMA_VERSION,
        "upstream_builds":("UMD-109","UMD-111"),
        "mode":"deterministic_read_only_market_dependency_model",
        "dependency_roles":DEPENDENCY_ROLES,
        "dependency_kinds":DEPENDENCY_KINDS,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,
        "persistence_enabled":False,
        "mutation_enabled":False,
        "publication_enabled":False,
        "execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_112_market_dependency_model()->bool:
    if verify_umd_111_semantic_registry() is not True:
        return False
    m=build_umd_112_certification_manifest()
    return m["build_id"]=="UMD-112" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
