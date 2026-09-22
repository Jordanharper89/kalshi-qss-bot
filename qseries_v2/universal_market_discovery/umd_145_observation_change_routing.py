from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_135_observation_routing_registry import ObservationRoutingRegistry
from .umd_144_observation_change_registry import ObservationChangeRegistry,ObservationChangeRecord,verify_umd_144_observation_change_registry

UMD_145_BUILD_ID="UMD-145"
UMD_145_REVISION="UMD_145_OBSERVATION_CHANGE_ROUTING_V1"
UMD_145_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class RoutedObservationChange:
    change_hash:str
    change_type:str
    subject_key:str
    observation_ids:Tuple[str,...]
    market_ids:Tuple[str,...]
    family_keys:Tuple[str,...]
    venue_keys:Tuple[str,...]

    def __post_init__(self):
        for name in ("observation_ids","market_ids","family_keys","venue_keys"):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)

    @property
    def route_hash(self)->str:
        return deterministic_sha256({
            "change_hash":self.change_hash,
            "change_type":self.change_type,
            "subject_key":self.subject_key,
            "observation_ids":self.observation_ids,
            "market_ids":self.market_ids,
            "family_keys":self.family_keys,
            "venue_keys":self.venue_keys,
        })

@dataclass(frozen=True,slots=True)
class ObservationChangeRouting:
    routes:Tuple[RoutedObservationChange,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"routes",tuple(self.routes))
        if self.routes!=tuple(sorted(self.routes,key=lambda r:(r.change_hash,r.route_hash))):
            raise ValueError("routes must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_145_BUILD_ID:
            raise ValueError("lineage must belong to UMD-145")
        required={r.change_hash for r in self.routes}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every change hash")

    @property
    def routing_hash(self)->str:
        return deterministic_sha256({
            "route_hashes":tuple(r.route_hash for r in self.routes),
            "lineage":self.lineage,
        })

class ObservationChangeRouter:
    __slots__=("change_registry","routing_registry")

    def __init__(self,change_registry:ObservationChangeRegistry,routing_registry:ObservationRoutingRegistry):
        if not isinstance(change_registry,ObservationChangeRegistry):
            raise TypeError("change_registry must be ObservationChangeRegistry")
        if not isinstance(routing_registry,ObservationRoutingRegistry):
            raise TypeError("routing_registry must be ObservationRoutingRegistry")
        self.change_registry=change_registry
        self.routing_registry=routing_registry

    def route(self,*,lineage:ImmutableLineage)->ObservationChangeRouting:
        record_by_obs={r.observation_id:r for r in self.routing_registry.records}
        routes=[]

        for change in self.change_registry.changes:
            observations=set()

            if change.change_type.startswith("canonical-"):
                observations.add(change.subject_key)
            elif change.change_type.startswith("contradiction-"):
                parts=tuple(x for x in change.subject_key.split("|") if x)
                observations.update(parts)
            # Cluster changes may not resolve to a single observation from the
            # change record alone; preserve them as structural changes with empty routing.

            markets=set(); families=set(); venues=set()
            known_obs=[]
            for obs in sorted(observations):
                record=record_by_obs.get(obs)
                if record is None:
                    continue
                known_obs.append(obs)
                markets.update(record.market_ids)
                families.update(record.family_keys)
                venues.update(record.venue_keys)

            routes.append(RoutedObservationChange(
                change.change_hash,
                change.change_type,
                change.subject_key,
                tuple(sorted(known_obs)),
                tuple(sorted(markets)),
                tuple(sorted(families)),
                tuple(sorted(venues)),
            ))

        routes.sort(key=lambda r:(r.change_hash,r.route_hash))
        return ObservationChangeRouting(tuple(routes),lineage)

def build_umd_145_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_145_BUILD_ID,"revision":UMD_145_REVISION,
        "schema_version":UMD_145_SCHEMA_VERSION,"upstream_builds":("UMD-135","UMD-144"),
        "mode":"deterministic_read_only_observation_change_routing",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_145_observation_change_routing()->bool:
    if verify_umd_144_observation_change_registry() is not True:
        return False
    m=build_umd_145_certification_manifest()
    return m["build_id"]=="UMD-145" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
