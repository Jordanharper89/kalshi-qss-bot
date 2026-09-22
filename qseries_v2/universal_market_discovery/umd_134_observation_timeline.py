from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from types import MappingProxyType
from typing import Iterable,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_132_observation_routing import ObservationRoute
from .umd_133_observation_priority import ObservationPriorityProfile,verify_umd_133_observation_priority_profile

UMD_134_BUILD_ID="UMD-134"
UMD_134_REVISION="UMD_134_OBSERVATION_TIMELINE_REGISTRY_V1"
UMD_134_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _utc(value:datetime)->datetime:
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True,slots=True)
class ObservationTimelineEntry:
    observation_id:str
    observed_at:datetime
    route_hash:str
    priority_profile_hash:str
    domain:str

    def __post_init__(self):
        object.__setattr__(self,"observed_at",_utc(self.observed_at))
        if not self.observation_id:
            raise ValueError("observation_id must be non-empty")
        if not self.domain:
            raise ValueError("domain must be non-empty")

    @property
    def entry_hash(self)->str:
        return deterministic_sha256({
            "observation_id":self.observation_id,
            "observed_at":self.observed_at,
            "route_hash":self.route_hash,
            "priority_profile_hash":self.priority_profile_hash,
            "domain":self.domain,
        })

@dataclass(frozen=True,slots=True)
class ObservationTimeline:
    timeline_id:str
    entries:Tuple[ObservationTimelineEntry,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"entries",tuple(self.entries))
        if not self.timeline_id:
            raise ValueError("timeline_id must be non-empty")
        expected=tuple(sorted(self.entries,key=lambda e:(e.observed_at,e.observation_id,e.entry_hash)))
        if self.entries!=expected:
            raise ValueError("timeline entries must be deterministically sorted")
        if len({e.observation_id for e in self.entries})!=len(self.entries):
            raise ValueError("timeline observation ids must be unique")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_134_BUILD_ID:
            raise ValueError("lineage must belong to UMD-134")
        required={e.route_hash for e in self.entries}|{e.priority_profile_hash for e in self.entries}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every route and priority profile hash")

    def observations_between(self,start:datetime,end:datetime)->Tuple[str,...]:
        start=_utc(start); end=_utc(end)
        if end<start:
            raise ValueError("end must be at or after start")
        return tuple(e.observation_id for e in self.entries if start<=e.observed_at<=end)

    @property
    def timeline_hash(self)->str:
        return deterministic_sha256({
            "timeline_id":self.timeline_id,
            "entry_hashes":tuple(e.entry_hash for e in self.entries),
            "lineage":self.lineage,
        })

class ObservationTimelineBuilder:
    __slots__=()

    def build(
        self,
        timeline_id:str,
        items:Iterable[tuple[ObservationRoute,ObservationPriorityProfile,datetime]],
        *,
        lineage_factory,
    )->ObservationTimeline:
        entries=[]
        for route,priority,observed_at in items:
            if not isinstance(route,ObservationRoute):
                raise TypeError("route must be ObservationRoute")
            if not isinstance(priority,ObservationPriorityProfile):
                raise TypeError("priority must be ObservationPriorityProfile")
            if priority.observation_id!=route.observation_id or priority.route_hash!=route.route_hash:
                raise ValueError("priority profile does not belong to route")
            entries.append(ObservationTimelineEntry(
                route.observation_id,observed_at,route.route_hash,priority.profile_hash,route.domain
            ))
        entries.sort(key=lambda e:(e.observed_at,e.observation_id,e.entry_hash))
        lineage=lineage_factory(tuple(
            h for e in entries for h in (e.route_hash,e.priority_profile_hash)
        ))
        return ObservationTimeline(timeline_id,tuple(entries),lineage)

def build_umd_134_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_134_BUILD_ID,"revision":UMD_134_REVISION,
        "schema_version":UMD_134_SCHEMA_VERSION,"upstream_builds":("UMD-132","UMD-133"),
        "mode":"deterministic_read_only_observation_timeline_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_134_observation_timeline_registry()->bool:
    if verify_umd_133_observation_priority_profile() is not True:
        return False
    m=build_umd_134_certification_manifest()
    return m["build_id"]=="UMD-134" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
