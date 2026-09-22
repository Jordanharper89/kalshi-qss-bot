from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_127_market_ladder import MarketLadder
from .umd_128_market_partition import MarketPartition, verify_umd_128_market_partition_model

UMD_129_BUILD_ID="UMD-129"
UMD_129_REVISION="UMD_129_MARKET_TOPOLOGY_REGISTRY_V1"
UMD_129_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze_index(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class MarketTopologyRegistry:
    ladders:Tuple[MarketLadder,...]
    partitions:Tuple[MarketPartition,...]
    market_to_ladders:Mapping[str,Tuple[str,...]]
    market_to_partitions:Mapping[str,Tuple[str,...]]
    family_to_ladders:Mapping[str,Tuple[str,...]]
    family_to_partitions:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"ladders",tuple(self.ladders))
        object.__setattr__(self,"partitions",tuple(self.partitions))
        for name in ("market_to_ladders","market_to_partitions","family_to_ladders","family_to_partitions"):
            object.__setattr__(self,name,_freeze_index(getattr(self,name)))
        if self.ladders!=tuple(sorted(self.ladders,key=lambda x:(x.family_key,x.ladder_hash))):
            raise ValueError("ladders must be deterministically sorted")
        if self.partitions!=tuple(sorted(self.partitions,key=lambda x:(x.family_key,x.partition_hash))):
            raise ValueError("partitions must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_129_BUILD_ID:
            raise ValueError("lineage must belong to UMD-129")
        required={x.ladder_hash for x in self.ladders}|{x.partition_hash for x in self.partitions}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every topology hash")

    def ladders_for_market(self,canonical_market_id:str)->Tuple[str,...]:
        return self.market_to_ladders.get(canonical_market_id,())

    def partitions_for_market(self,canonical_market_id:str)->Tuple[str,...]:
        return self.market_to_partitions.get(canonical_market_id,())

    def ladders_for_family(self,family_key:str)->Tuple[str,...]:
        return self.family_to_ladders.get(family_key,())

    def partitions_for_family(self,family_key:str)->Tuple[str,...]:
        return self.family_to_partitions.get(family_key,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "ladder_hashes":tuple(x.ladder_hash for x in self.ladders),
            "partition_hashes":tuple(x.partition_hash for x in self.partitions),
            "market_to_ladders":self.market_to_ladders,
            "market_to_partitions":self.market_to_partitions,
            "family_to_ladders":self.family_to_ladders,
            "family_to_partitions":self.family_to_partitions,
            "lineage":self.lineage,
        })

class MarketTopologyRegistryBuilder:
    __slots__=()

    def build(
        self,
        ladders:Iterable[MarketLadder],
        partitions:Iterable[MarketPartition],
        *,
        lineage_factory,
    )->MarketTopologyRegistry:
        ls=tuple(ladders)
        ps=tuple(partitions)
        if any(not isinstance(x,MarketLadder) for x in ls):
            raise TypeError("ladders must contain MarketLadder")
        if any(not isinstance(x,MarketPartition) for x in ps):
            raise TypeError("partitions must contain MarketPartition")

        ls=tuple(sorted(ls,key=lambda x:(x.family_key,x.ladder_hash)))
        ps=tuple(sorted(ps,key=lambda x:(x.family_key,x.partition_hash)))

        market_l={}
        market_p={}
        family_l={}
        family_p={}

        for ladder in ls:
            family_l.setdefault(ladder.family_key,[]).append(ladder.ladder_hash)
            for rung in ladder.rungs:
                market_l.setdefault(rung.canonical_market_id,[]).append(ladder.ladder_hash)

        for partition in ps:
            family_p.setdefault(partition.family_key,[]).append(partition.partition_hash)
            for member in partition.members:
                market_p.setdefault(member.canonical_market_id,[]).append(partition.partition_hash)

        for index in (market_l,market_p,family_l,family_p):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        parent_hashes=tuple(x.ladder_hash for x in ls)+tuple(x.partition_hash for x in ps)
        lineage=lineage_factory(parent_hashes)
        return MarketTopologyRegistry(ls,ps,market_l,market_p,family_l,family_p,lineage)

def build_umd_129_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_129_BUILD_ID,"revision":UMD_129_REVISION,
        "schema_version":UMD_129_SCHEMA_VERSION,"upstream_builds":("UMD-127","UMD-128"),
        "mode":"deterministic_read_only_market_topology_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_129_market_topology_registry()->bool:
    if verify_umd_128_market_partition_model() is not True:
        return False
    m=build_umd_129_certification_manifest()
    return m["build_id"]=="UMD-129" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
