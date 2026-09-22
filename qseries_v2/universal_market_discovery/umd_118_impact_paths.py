from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_115_observation_impact import DirectImpactResult
from .umd_116_dependency_propagation import PropagationResult,PropagationStep
from .umd_117_impact_registry import verify_umd_117_impact_registry

UMD_118_BUILD_ID="UMD-118"
UMD_118_REVISION="UMD_118_IMPACT_PATH_RESOLUTION_V1"
UMD_118_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ImpactPath:
    observation_hash:str
    target_market_id:str
    direct:bool
    market_path:Tuple[str,...]
    constraint_path:Tuple[str,...]

    def __post_init__(self):
        object.__setattr__(self,"market_path",tuple(self.market_path))
        object.__setattr__(self,"constraint_path",tuple(self.constraint_path))
        if not self.market_path:
            raise ValueError("market_path must be non-empty")
        if self.market_path[-1]!=self.target_market_id:
            raise ValueError("target market must terminate market_path")
        if len(self.constraint_path)!=len(self.market_path)-1:
            raise ValueError("constraint_path length must be market_path length minus one")
        if self.direct and len(self.market_path)!=1:
            raise ValueError("direct impact path must contain exactly one market")
        if not self.direct and len(self.market_path)<2:
            raise ValueError("propagated impact path must contain at least two markets")

    @property
    def path_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "target_market_id":self.target_market_id,
            "direct":self.direct,
            "market_path":self.market_path,
            "constraint_path":self.constraint_path,
        })

@dataclass(frozen=True,slots=True)
class ImpactPathSet:
    observation_hash:str
    paths:Tuple[ImpactPath,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"paths",tuple(self.paths))
        if tuple(sorted(self.paths,key=lambda p:(p.target_market_id,not p.direct,p.market_path,p.constraint_path)))!=self.paths:
            raise ValueError("paths must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_118_BUILD_ID:
            raise ValueError("lineage must belong to UMD-118")

    def paths_to(self,canonical_market_id:str)->Tuple[ImpactPath,...]:
        return tuple(p for p in self.paths if p.target_market_id==canonical_market_id)

    @property
    def path_set_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "path_hashes":tuple(p.path_hash for p in self.paths),
            "lineage":self.lineage,
        })

class ImpactPathResolver:
    __slots__=()

    def resolve(
        self,
        direct:DirectImpactResult,
        propagation:PropagationResult,
        *,
        lineage:ImmutableLineage,
    )->ImpactPathSet:
        if not isinstance(direct,DirectImpactResult):
            raise TypeError("direct must be DirectImpactResult")
        if not isinstance(propagation,PropagationResult):
            raise TypeError("propagation must be PropagationResult")
        if tuple(direct.market_ids)!=tuple(propagation.direct_market_ids):
            raise ValueError("direct and propagation market sets do not align")

        paths={}
        for market_id in direct.market_ids:
            paths[market_id]=ImpactPath(
                direct.observation_hash,market_id,True,(market_id,),()
            )

        ordered=tuple(sorted(
            propagation.steps,
            key=lambda s:(s.depth,s.source_market_id,s.target_market_id,s.constraint_type)
        ))

        for step in ordered:
            source_path=paths.get(step.source_market_id)
            if source_path is None:
                raise ValueError("propagation step source is not reachable from direct impact")
            candidate=ImpactPath(
                direct.observation_hash,
                step.target_market_id,
                False,
                source_path.market_path+(step.target_market_id,),
                source_path.constraint_path+(step.constraint_type,),
            )
            existing=paths.get(step.target_market_id)
            if existing is None or (len(candidate.market_path),candidate.market_path,candidate.constraint_path) < (
                len(existing.market_path),existing.market_path,existing.constraint_path
            ):
                paths[step.target_market_id]=candidate

        expected=set(propagation.all_market_ids)
        if set(paths)!=expected:
            raise ValueError("resolved impact paths do not cover propagation result")

        values=tuple(sorted(paths.values(),key=lambda p:(p.target_market_id,not p.direct,p.market_path,p.constraint_path)))
        return ImpactPathSet(direct.observation_hash,values,lineage)

def build_umd_118_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_118_BUILD_ID,"revision":UMD_118_REVISION,
        "schema_version":UMD_118_SCHEMA_VERSION,"upstream_builds":("UMD-115","UMD-116","UMD-117"),
        "mode":"deterministic_read_only_impact_path_resolution",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_118_impact_path_resolution()->bool:
    if verify_umd_117_impact_registry() is not True:
        return False
    m=build_umd_118_certification_manifest()
    return m["build_id"]=="UMD-118" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
