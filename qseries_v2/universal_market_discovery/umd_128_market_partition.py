from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_109_market_semantic_profile import MarketSemanticProfile
from .umd_110_market_family_resolution import MarketFamily
from .umd_127_market_ladder import verify_umd_127_market_ladder_model

UMD_128_BUILD_ID="UMD-128"
UMD_128_REVISION="UMD_128_MARKET_PARTITION_MODEL_V1"
UMD_128_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class PartitionMember:
    canonical_market_id:str
    outcome_key:str
    profile_hash:str

    @property
    def member_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "outcome_key":self.outcome_key,
            "profile_hash":self.profile_hash,
        })

@dataclass(frozen=True,slots=True)
class MarketPartition:
    family_key:str
    members:Tuple[PartitionMember,...]
    mutually_exclusive:bool
    collectively_exhaustive:bool
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"members",tuple(self.members))
        if len(self.members)<2:
            raise ValueError("market partition requires at least two members")
        if self.members!=tuple(sorted(self.members,key=lambda m:(m.outcome_key,m.canonical_market_id))):
            raise ValueError("partition members must be deterministically sorted")
        outcomes=[m.outcome_key for m in self.members]
        if len(outcomes)!=len(set(outcomes)):
            raise ValueError("partition outcomes must be unique")
        markets=[m.canonical_market_id for m in self.members]
        if len(markets)!=len(set(markets)):
            raise ValueError("partition market ids must be unique")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_128_BUILD_ID:
            raise ValueError("lineage must belong to UMD-128")
        required={m.profile_hash for m in self.members}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every partition profile hash")

    def market_for_outcome(self,outcome_key:str)->str|None:
        for member in self.members:
            if member.outcome_key==outcome_key:
                return member.canonical_market_id
        return None

    @property
    def partition_hash(self)->str:
        return deterministic_sha256({
            "family_key":self.family_key,
            "member_hashes":tuple(m.member_hash for m in self.members),
            "mutually_exclusive":self.mutually_exclusive,
            "collectively_exhaustive":self.collectively_exhaustive,
            "lineage":self.lineage,
        })

class MarketPartitionBuilder:
    __slots__=()

    def build(
        self,
        family:MarketFamily,
        profiles:Iterable[MarketSemanticProfile],
        *,
        outcome_kind:str="event",
        mutually_exclusive:bool=True,
        collectively_exhaustive:bool=True,
        lineage:ImmutableLineage,
    )->MarketPartition:
        if not isinstance(family,MarketFamily):
            raise TypeError("family must be MarketFamily")
        ps=tuple(profiles)
        if any(not isinstance(p,MarketSemanticProfile) for p in ps):
            raise TypeError("profiles must contain MarketSemanticProfile")

        members=set(family.member_market_ids)
        selected=[p for p in ps if p.canonical_market_id in members]
        if {p.canonical_market_id for p in selected}!=members:
            raise ValueError("profiles must cover every family member")

        result=[]
        for profile in selected:
            values=profile.values(outcome_kind)
            if len(values)!=1:
                raise ValueError("partition profile requires exactly one outcome semantic value")
            result.append(PartitionMember(
                profile.canonical_market_id,
                values[0],
                profile.profile_hash,
            ))
        result.sort(key=lambda m:(m.outcome_key,m.canonical_market_id))
        return MarketPartition(
            family.family_key,
            tuple(result),
            bool(mutually_exclusive),
            bool(collectively_exhaustive),
            lineage,
        )

def build_umd_128_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_128_BUILD_ID,"revision":UMD_128_REVISION,
        "schema_version":UMD_128_SCHEMA_VERSION,"upstream_builds":("UMD-109","UMD-110","UMD-127"),
        "mode":"deterministic_read_only_market_partition_model",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_128_market_partition_model()->bool:
    if verify_umd_127_market_ladder_model() is not True:
        return False
    m=build_umd_128_certification_manifest()
    return m["build_id"]=="UMD-128" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
