from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_115_observation_impact import DirectImpactResult
from .umd_116_dependency_propagation import PropagationResult, verify_umd_116_dependency_propagation

UMD_117_BUILD_ID="UMD-117"
UMD_117_REVISION="UMD_117_IMPACT_REGISTRY_V1"
UMD_117_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze_index(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ImpactRecord:
    observation_hash:str
    direct_market_ids:Tuple[str,...]
    propagated_market_ids:Tuple[str,...]
    direct_impact_hash:str
    propagation_hash:str

    @property
    def all_market_ids(self)->Tuple[str,...]:
        return tuple(sorted(set(self.direct_market_ids)|set(self.propagated_market_ids)))

    @property
    def record_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "direct_market_ids":self.direct_market_ids,
            "propagated_market_ids":self.propagated_market_ids,
            "direct_impact_hash":self.direct_impact_hash,
            "propagation_hash":self.propagation_hash,
        })

@dataclass(frozen=True,slots=True)
class ImpactRegistry:
    records:Tuple[ImpactRecord,...]
    observation_index:Mapping[str,Tuple[str,...]]
    market_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"records",tuple(self.records))
        object.__setattr__(self,"observation_index",_freeze_index(self.observation_index))
        object.__setattr__(self,"market_index",_freeze_index(self.market_index))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_117_BUILD_ID:
            raise ValueError("lineage must belong to UMD-117")
        required={r.record_hash for r in self.records}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every impact record hash")

    def markets_for_observation(self,observation_hash:str)->Tuple[str,...]:
        return self.observation_index.get(observation_hash,())

    def observations_for_market(self,canonical_market_id:str)->Tuple[str,...]:
        return self.market_index.get(canonical_market_id,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "record_hashes":tuple(r.record_hash for r in self.records),
            "observation_index":self.observation_index,
            "market_index":self.market_index,
            "lineage":self.lineage,
        })

class ImpactRegistryBuilder:
    __slots__=()

    def build(
        self,
        pairs:Iterable[tuple[DirectImpactResult,PropagationResult]],
        *,
        lineage_factory,
    )->ImpactRegistry:
        records=[]
        observation_index={}
        market_index={}

        for direct,propagation in pairs:
            if not isinstance(direct,DirectImpactResult):
                raise TypeError("direct impact must be DirectImpactResult")
            if not isinstance(propagation,PropagationResult):
                raise TypeError("propagation must be PropagationResult")
            if tuple(direct.market_ids)!=tuple(propagation.direct_market_ids):
                raise ValueError("propagation direct markets do not match direct impact")

            record=ImpactRecord(
                direct.observation_hash,
                tuple(direct.market_ids),
                tuple(propagation.propagated_market_ids),
                direct.impact_hash,
                propagation.propagation_hash,
            )
            records.append(record)
            observation_index.setdefault(record.observation_hash,[]).extend(record.all_market_ids)
            for market_id in record.all_market_ids:
                market_index.setdefault(market_id,[]).append(record.observation_hash)

        records.sort(key=lambda r:(r.observation_hash,r.record_hash))
        for index in (observation_index,market_index):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        lineage=lineage_factory(tuple(r.record_hash for r in records))
        return ImpactRegistry(tuple(records),observation_index,market_index,lineage)

def build_umd_117_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_117_BUILD_ID,"revision":UMD_117_REVISION,
        "schema_version":UMD_117_SCHEMA_VERSION,"upstream_builds":("UMD-115","UMD-116"),
        "mode":"deterministic_read_only_impact_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_117_impact_registry()->bool:
    if verify_umd_116_dependency_propagation() is not True:
        return False
    m=build_umd_117_certification_manifest()
    return m["build_id"]=="UMD-117" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
