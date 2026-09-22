from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_129_market_topology import MarketTopologyRegistry
from .umd_162_convergence_change_registry import ConvergenceChangeRegistry,verify_umd_162_convergence_change_registry

UMD_163_BUILD_ID="UMD-163"
UMD_163_REVISION="UMD_163_CONVERGENCE_TOPOLOGY_PROJECTION_V1"
UMD_163_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ConvergenceTopologyProjection:
    market_ids:Tuple[str,...]
    ladder_hashes:Tuple[str,...]
    partition_hashes:Tuple[str,...]
    market_to_change_types:Mapping[str,Tuple[str,...]]
    market_to_ladders:Mapping[str,Tuple[str,...]]
    market_to_partitions:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        for name in ("market_ids","ladder_hashes","partition_hashes"):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        for name in ("market_to_change_types","market_to_ladders","market_to_partitions"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_163_BUILD_ID:
            raise ValueError("lineage must belong to UMD-163")

    @property
    def projection_hash(self)->str:
        return deterministic_sha256({
            "market_ids":self.market_ids,
            "ladder_hashes":self.ladder_hashes,
            "partition_hashes":self.partition_hashes,
            "market_to_change_types":self.market_to_change_types,
            "market_to_ladders":self.market_to_ladders,
            "market_to_partitions":self.market_to_partitions,
            "lineage":self.lineage,
        })

class ConvergenceTopologyProjector:
    __slots__=("change_registry","topology_registry")

    def __init__(self,change_registry:ConvergenceChangeRegistry,topology_registry:MarketTopologyRegistry):
        if not isinstance(change_registry,ConvergenceChangeRegistry):
            raise TypeError("change_registry must be ConvergenceChangeRegistry")
        if not isinstance(topology_registry,MarketTopologyRegistry):
            raise TypeError("topology_registry must be MarketTopologyRegistry")
        self.change_registry=change_registry
        self.topology_registry=topology_registry

    def project(self,*,lineage:ImmutableLineage)->ConvergenceTopologyProjection:
        change_types={}
        for record in self.change_registry.records:
            change_types.setdefault(record.canonical_market_id,[]).append(record.change_type)

        markets=tuple(sorted(change_types))
        ladders=set(); partitions=set()
        market_to_ladders={}; market_to_partitions={}

        for market_id in markets:
            ls=self.topology_registry.ladders_for_market(market_id)
            ps=self.topology_registry.partitions_for_market(market_id)
            if ls:
                market_to_ladders[market_id]=ls
                ladders.update(ls)
            if ps:
                market_to_partitions[market_id]=ps
                partitions.update(ps)

        for market_id,types in change_types.items():
            change_types[market_id]=tuple(sorted(set(types)))

        return ConvergenceTopologyProjection(
            markets,
            tuple(sorted(ladders)),
            tuple(sorted(partitions)),
            change_types,
            market_to_ladders,
            market_to_partitions,
            lineage,
        )

def build_umd_163_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_163_BUILD_ID,"revision":UMD_163_REVISION,
        "schema_version":UMD_163_SCHEMA_VERSION,"upstream_builds":("UMD-129","UMD-162"),
        "mode":"deterministic_read_only_convergence_topology_projection",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_163_convergence_topology_projection()->bool:
    if verify_umd_162_convergence_change_registry() is not True:
        return False
    m=build_umd_163_certification_manifest()
    return m["build_id"]=="UMD-163" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
