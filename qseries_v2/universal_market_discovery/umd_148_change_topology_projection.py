from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_129_market_topology import MarketTopologyRegistry
from .umd_147_observation_change_impact_registry import ObservationChangeImpactRegistry,verify_umd_147_observation_change_impact_registry

UMD_148_BUILD_ID="UMD-148"
UMD_148_REVISION="UMD_148_CHANGE_TOPOLOGY_PROJECTION_V1"
UMD_148_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ChangeTopologyProjection:
    change_hash:str
    market_ids:Tuple[str,...]
    ladder_hashes:Tuple[str,...]
    partition_hashes:Tuple[str,...]
    market_to_ladders:Mapping[str,Tuple[str,...]]
    market_to_partitions:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"market_ids",tuple(self.market_ids))
        object.__setattr__(self,"ladder_hashes",tuple(self.ladder_hashes))
        object.__setattr__(self,"partition_hashes",tuple(self.partition_hashes))
        object.__setattr__(self,"market_to_ladders",_freeze(self.market_to_ladders))
        object.__setattr__(self,"market_to_partitions",_freeze(self.market_to_partitions))
        for name in ("market_ids","ladder_hashes","partition_hashes"):
            value=getattr(self,name)
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_148_BUILD_ID:
            raise ValueError("lineage must belong to UMD-148")

    @property
    def projection_hash(self)->str:
        return deterministic_sha256({
            "change_hash":self.change_hash,
            "market_ids":self.market_ids,
            "ladder_hashes":self.ladder_hashes,
            "partition_hashes":self.partition_hashes,
            "market_to_ladders":self.market_to_ladders,
            "market_to_partitions":self.market_to_partitions,
            "lineage":self.lineage,
        })

class ChangeTopologyProjector:
    __slots__=("impact_registry","topology_registry")

    def __init__(self,impact_registry:ObservationChangeImpactRegistry,topology_registry:MarketTopologyRegistry):
        if not isinstance(impact_registry,ObservationChangeImpactRegistry):
            raise TypeError("impact_registry must be ObservationChangeImpactRegistry")
        if not isinstance(topology_registry,MarketTopologyRegistry):
            raise TypeError("topology_registry must be MarketTopologyRegistry")
        self.impact_registry=impact_registry
        self.topology_registry=topology_registry

    def project(self,change_hash:str,*,lineage:ImmutableLineage)->ChangeTopologyProjection:
        markets=tuple(sorted({
            market_id
            for market_id,changes in self.impact_registry.market_index.items()
            if change_hash in changes
        }))
        market_to_ladders={}
        market_to_partitions={}
        ladders=set()
        partitions=set()

        for market_id in markets:
            ls=self.topology_registry.ladders_for_market(market_id)
            ps=self.topology_registry.partitions_for_market(market_id)
            if ls:
                market_to_ladders[market_id]=ls
                ladders.update(ls)
            if ps:
                market_to_partitions[market_id]=ps
                partitions.update(ps)

        return ChangeTopologyProjection(
            change_hash,
            markets,
            tuple(sorted(ladders)),
            tuple(sorted(partitions)),
            market_to_ladders,
            market_to_partitions,
            lineage,
        )

def build_umd_148_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_148_BUILD_ID,"revision":UMD_148_REVISION,
        "schema_version":UMD_148_SCHEMA_VERSION,"upstream_builds":("UMD-129","UMD-147"),
        "mode":"deterministic_read_only_change_topology_projection",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_148_change_topology_projection()->bool:
    if verify_umd_147_observation_change_impact_registry() is not True:
        return False
    m=build_umd_148_certification_manifest()
    return m["build_id"]=="UMD-148" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
