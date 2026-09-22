from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_109_market_semantic_profile import MarketSemanticProfile
from .umd_110_market_family_resolution import MarketFamily
from .umd_112_market_dependency import verify_umd_112_market_dependency_model

UMD_113_BUILD_ID="UMD-113"
UMD_113_REVISION="UMD_113_MARKET_CONSTRAINT_GRAPH_V1"
UMD_113_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
CONSTRAINT_TYPES=("threshold_monotonic","mutually_exclusive","implies","equivalent","collectively_exhaustive")
SYMMETRIC_CONSTRAINT_TYPES=("mutually_exclusive","equivalent")

@dataclass(frozen=True,slots=True)
class MarketConstraint:
    source_market_id:str
    target_market_id:str
    constraint_type:str
    basis:str

    def __post_init__(self):
        if not self.source_market_id or not self.target_market_id:
            raise ValueError("constraint endpoints must be non-empty")
        if self.source_market_id==self.target_market_id:
            raise ValueError("constraint endpoints must differ")
        if self.constraint_type not in CONSTRAINT_TYPES:
            raise ValueError("unsupported constraint type")
        if not isinstance(self.basis,str) or not self.basis.strip():
            raise ValueError("constraint basis must be non-empty")

    @property
    def constraint_hash(self)->str:
        return deterministic_sha256({
            "source_market_id":self.source_market_id,
            "target_market_id":self.target_market_id,
            "constraint_type":self.constraint_type,
            "basis":self.basis,
        })

@dataclass(frozen=True,slots=True)
class MarketConstraintGraph:
    market_ids:Tuple[str,...]
    constraints:Tuple[MarketConstraint,...]
    family_hashes:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"market_ids",tuple(self.market_ids))
        object.__setattr__(self,"constraints",tuple(self.constraints))
        object.__setattr__(self,"family_hashes",tuple(self.family_hashes))
        if tuple(sorted(self.market_ids))!=self.market_ids:
            raise ValueError("market_ids must be sorted")
        if len(set(self.market_ids))!=len(self.market_ids):
            raise ValueError("market_ids must be unique")
        known=set(self.market_ids)
        for c in self.constraints:
            if c.source_market_id not in known or c.target_market_id not in known:
                raise ValueError("constraint references unknown market")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_113_BUILD_ID:
            raise ValueError("lineage must belong to UMD-113")
        if not set(self.family_hashes).issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every family hash")

    def constraints_for(self,canonical_market_id:str)->Tuple[MarketConstraint,...]:
        return tuple(
            c for c in self.constraints
            if c.source_market_id==canonical_market_id or c.target_market_id==canonical_market_id
        )

    @property
    def graph_hash(self)->str:
        return deterministic_sha256({
            "market_ids":self.market_ids,
            "constraint_hashes":tuple(c.constraint_hash for c in self.constraints),
            "family_hashes":self.family_hashes,
            "lineage":self.lineage,
        })

class MarketConstraintGraphBuilder:
    __slots__=()

    def build(
        self,
        profiles:Iterable[MarketSemanticProfile],
        families:Iterable[MarketFamily],
        specs:Iterable[tuple[str,str,str,str]],
        *,
        lineage:ImmutableLineage,
    )->MarketConstraintGraph:
        ps=tuple(profiles)
        fs=tuple(families)
        if any(not isinstance(p,MarketSemanticProfile) for p in ps):
            raise TypeError("profiles must contain MarketSemanticProfile")
        if any(not isinstance(f,MarketFamily) for f in fs):
            raise TypeError("families must contain MarketFamily")

        market_ids=tuple(sorted({p.canonical_market_id for p in ps}))
        known=set(market_ids)
        constraints=[]
        seen=set()

        for source,target,constraint_type,basis in specs:
            if source not in known or target not in known:
                raise ValueError("constraint specification references unknown market")
            if constraint_type in SYMMETRIC_CONSTRAINT_TYPES and target<source:
                source,target=target,source
            key=(source,target,constraint_type,basis)
            if key in seen:
                continue
            seen.add(key)
            constraints.append(MarketConstraint(source,target,constraint_type,basis))

        constraints.sort(key=lambda c:(c.source_market_id,c.target_market_id,c.constraint_type,c.basis))
        return MarketConstraintGraph(
            market_ids,
            tuple(constraints),
            tuple(sorted(f.family_hash for f in fs)),
            lineage,
        )

def build_umd_113_certification_manifest():
    data={
        "subsystem_id":"UMD",
        "build_id":UMD_113_BUILD_ID,
        "revision":UMD_113_REVISION,
        "schema_version":UMD_113_SCHEMA_VERSION,
        "upstream_builds":("UMD-109","UMD-110","UMD-112"),
        "mode":"deterministic_read_only_market_constraint_graph",
        "constraint_types":CONSTRAINT_TYPES,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,
        "persistence_enabled":False,
        "mutation_enabled":False,
        "publication_enabled":False,
        "execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_113_market_constraint_graph()->bool:
    if verify_umd_112_market_dependency_model() is not True:
        return False
    m=build_umd_113_certification_manifest()
    return m["build_id"]=="UMD-113" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
