from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_130_observation_classification import CanonicalObservationClassification
from .umd_131_observation_entity_resolution import ObservationEntityResolution
from .umd_132_observation_routing import ObservationRoute
from .umd_133_observation_priority import ObservationPriorityProfile
from .umd_134_observation_timeline import ObservationTimeline,verify_umd_134_observation_timeline_registry

UMD_135_BUILD_ID="UMD-135"
UMD_135_REVISION="UMD_135_OBSERVATION_ROUTING_REGISTRY_V1"
UMD_135_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ObservationRoutingRecord:
    observation_id:str
    domain:str
    classification_hash:str
    entity_resolution_hash:str
    route_hash:str
    priority_profile_hash:str
    timeline_id:str
    market_ids:Tuple[str,...]
    family_keys:Tuple[str,...]
    venue_keys:Tuple[str,...]
    unresolved_entities:Tuple[Tuple[str,str],...]

    @property
    def record_hash(self)->str:
        return deterministic_sha256({
            "observation_id":self.observation_id,
            "domain":self.domain,
            "classification_hash":self.classification_hash,
            "entity_resolution_hash":self.entity_resolution_hash,
            "route_hash":self.route_hash,
            "priority_profile_hash":self.priority_profile_hash,
            "timeline_id":self.timeline_id,
            "market_ids":self.market_ids,
            "family_keys":self.family_keys,
            "venue_keys":self.venue_keys,
            "unresolved_entities":self.unresolved_entities,
        })

@dataclass(frozen=True,slots=True)
class ObservationRoutingRegistry:
    records:Tuple[ObservationRoutingRecord,...]
    market_index:Mapping[str,Tuple[str,...]]
    family_index:Mapping[str,Tuple[str,...]]
    venue_index:Mapping[str,Tuple[str,...]]
    domain_index:Mapping[str,Tuple[str,...]]
    timeline_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"records",tuple(self.records))
        for name in ("market_index","family_index","venue_index","domain_index","timeline_index"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.records!=tuple(sorted(self.records,key=lambda r:(r.observation_id,r.record_hash))):
            raise ValueError("records must be deterministically sorted")
        if len({r.observation_id for r in self.records})!=len(self.records):
            raise ValueError("observation ids must be unique")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_135_BUILD_ID:
            raise ValueError("lineage must belong to UMD-135")
        required={r.record_hash for r in self.records}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every routing record hash")

    def observations_for_market(self,key:str)->Tuple[str,...]: return self.market_index.get(key,())
    def observations_for_family(self,key:str)->Tuple[str,...]: return self.family_index.get(key,())
    def observations_for_venue(self,key:str)->Tuple[str,...]: return self.venue_index.get(key,())
    def observations_for_domain(self,key:str)->Tuple[str,...]: return self.domain_index.get(key,())
    def observations_for_timeline(self,key:str)->Tuple[str,...]: return self.timeline_index.get(key,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "record_hashes":tuple(r.record_hash for r in self.records),
            "market_index":self.market_index,
            "family_index":self.family_index,
            "venue_index":self.venue_index,
            "domain_index":self.domain_index,
            "timeline_index":self.timeline_index,
            "lineage":self.lineage,
        })

class ObservationRoutingRegistryBuilder:
    __slots__=()

    def build(
        self,
        items:Iterable[tuple[
            CanonicalObservationClassification,
            ObservationEntityResolution,
            ObservationRoute,
            ObservationPriorityProfile,
            ObservationTimeline,
        ]],
        *,
        lineage_factory,
    )->ObservationRoutingRegistry:
        records=[]
        market={}; family={}; venue={}; domain={}; timeline={}

        for classification,entities,route,priority,timeline_obj in items:
            if not isinstance(classification,CanonicalObservationClassification): raise TypeError("classification must be CanonicalObservationClassification")
            if not isinstance(entities,ObservationEntityResolution): raise TypeError("entities must be ObservationEntityResolution")
            if not isinstance(route,ObservationRoute): raise TypeError("route must be ObservationRoute")
            if not isinstance(priority,ObservationPriorityProfile): raise TypeError("priority must be ObservationPriorityProfile")
            if not isinstance(timeline_obj,ObservationTimeline): raise TypeError("timeline must be ObservationTimeline")

            obs=classification.observation_id
            if not (entities.observation_id==route.observation_id==priority.observation_id==obs):
                raise ValueError("observation components do not belong to same observation")
            if entities.classification_hash!=classification.classification_hash:
                raise ValueError("entity resolution classification mismatch")
            if route.classification_hash!=classification.classification_hash or route.entity_resolution_hash!=entities.resolution_hash:
                raise ValueError("route ownership mismatch")
            if priority.route_hash!=route.route_hash:
                raise ValueError("priority ownership mismatch")
            if obs not in {e.observation_id for e in timeline_obj.entries}:
                raise ValueError("timeline does not contain observation")

            rec=ObservationRoutingRecord(
                obs,classification.domain,classification.classification_hash,entities.resolution_hash,
                route.route_hash,priority.profile_hash,timeline_obj.timeline_id,route.market_ids,
                route.family_keys,route.venues(),route.unresolved_entities
            )
            records.append(rec)

            for x in rec.market_ids: market.setdefault(x,[]).append(obs)
            for x in rec.family_keys: family.setdefault(x,[]).append(obs)
            for x in rec.venue_keys: venue.setdefault(x,[]).append(obs)
            domain.setdefault(rec.domain,[]).append(obs)
            timeline.setdefault(rec.timeline_id,[]).append(obs)

        records.sort(key=lambda r:(r.observation_id,r.record_hash))
        for index in (market,family,venue,domain,timeline):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        lineage=lineage_factory(tuple(r.record_hash for r in records))
        return ObservationRoutingRegistry(tuple(records),market,family,venue,domain,timeline,lineage)

def build_umd_135_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_135_BUILD_ID,"revision":UMD_135_REVISION,
        "schema_version":UMD_135_SCHEMA_VERSION,"upstream_builds":("UMD-130","UMD-131","UMD-132","UMD-133","UMD-134"),
        "mode":"deterministic_read_only_observation_routing_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_135_observation_routing_registry()->bool:
    if verify_umd_134_observation_timeline_registry() is not True:
        return False
    m=build_umd_135_certification_manifest()
    return m["build_id"]=="UMD-135" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
