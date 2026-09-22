from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_113_market_constraints import MarketConstraintGraph
from .umd_115_observation_impact import DirectImpactResult, verify_umd_115_observation_impact_mapping

UMD_116_BUILD_ID="UMD-116"
UMD_116_REVISION="UMD_116_DEPENDENCY_PROPAGATION_V1"
UMD_116_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
PROPAGATING_CONSTRAINTS=("threshold_monotonic","implies","equivalent")

@dataclass(frozen=True,slots=True)
class PropagationStep:
    depth:int
    source_market_id:str
    target_market_id:str
    constraint_type:str

    @property
    def step_hash(self)->str:
        return deterministic_sha256({
            "depth":self.depth,
            "source_market_id":self.source_market_id,
            "target_market_id":self.target_market_id,
            "constraint_type":self.constraint_type,
        })

@dataclass(frozen=True,slots=True)
class PropagationResult:
    direct_market_ids:Tuple[str,...]
    propagated_market_ids:Tuple[str,...]
    steps:Tuple[PropagationStep,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"direct_market_ids",tuple(self.direct_market_ids))
        object.__setattr__(self,"propagated_market_ids",tuple(self.propagated_market_ids))
        object.__setattr__(self,"steps",tuple(self.steps))
        if tuple(sorted(set(self.direct_market_ids)))!=self.direct_market_ids:
            raise ValueError("direct_market_ids must be unique and sorted")
        if tuple(sorted(set(self.propagated_market_ids)))!=self.propagated_market_ids:
            raise ValueError("propagated_market_ids must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_116_BUILD_ID:
            raise ValueError("lineage must belong to UMD-116")

    @property
    def all_market_ids(self)->Tuple[str,...]:
        return tuple(sorted(set(self.direct_market_ids)|set(self.propagated_market_ids)))

    @property
    def propagation_hash(self)->str:
        return deterministic_sha256({
            "direct_market_ids":self.direct_market_ids,
            "propagated_market_ids":self.propagated_market_ids,
            "steps":tuple({
                "depth":s.depth,
                "source_market_id":s.source_market_id,
                "target_market_id":s.target_market_id,
                "constraint_type":s.constraint_type,
            } for s in self.steps),
            "lineage":self.lineage,
        })

class DependencyPropagationEngine:
    __slots__=("graph",)

    def __init__(self,graph:MarketConstraintGraph):
        if not isinstance(graph,MarketConstraintGraph):
            raise TypeError("graph must be MarketConstraintGraph")
        self.graph=graph

    def propagate(
        self,
        direct:DirectImpactResult,
        *,
        max_depth:int=3,
        lineage:ImmutableLineage,
    )->PropagationResult:
        if not isinstance(direct,DirectImpactResult):
            raise TypeError("direct must be DirectImpactResult")
        if not isinstance(max_depth,int) or max_depth<0:
            raise ValueError("max_depth must be a non-negative integer")

        adjacency={}
        for c in self.graph.constraints:
            if c.constraint_type not in PROPAGATING_CONSTRAINTS:
                continue
            adjacency.setdefault(c.source_market_id,[]).append((c.target_market_id,c.constraint_type))
            if c.constraint_type=="equivalent":
                adjacency.setdefault(c.target_market_id,[]).append((c.source_market_id,c.constraint_type))

        direct_set=set(direct.market_ids)
        seen=set(direct_set)
        frontier=tuple(sorted(direct_set))
        steps=[]

        for depth in range(1,max_depth+1):
            next_frontier=set()
            for source in frontier:
                for target,constraint_type in sorted(adjacency.get(source,())):
                    if target in seen:
                        continue
                    seen.add(target)
                    next_frontier.add(target)
                    steps.append(PropagationStep(depth,source,target,constraint_type))
            if not next_frontier:
                break
            frontier=tuple(sorted(next_frontier))

        propagated=tuple(sorted(seen-direct_set))
        steps.sort(key=lambda s:(s.depth,s.source_market_id,s.target_market_id,s.constraint_type))
        return PropagationResult(tuple(sorted(direct_set)),propagated,tuple(steps),lineage)

def build_umd_116_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_116_BUILD_ID,"revision":UMD_116_REVISION,
        "schema_version":UMD_116_SCHEMA_VERSION,"upstream_builds":("UMD-113","UMD-115"),
        "mode":"deterministic_read_only_dependency_propagation",
        "propagating_constraints":PROPAGATING_CONSTRAINTS,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_116_dependency_propagation()->bool:
    if verify_umd_115_observation_impact_mapping() is not True:
        return False
    m=build_umd_116_certification_manifest()
    return m["build_id"]=="UMD-116" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
