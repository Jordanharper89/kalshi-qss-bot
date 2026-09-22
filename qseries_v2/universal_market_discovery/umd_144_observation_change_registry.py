from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_143_observation_state_diff import ObservationStateDiff,verify_umd_143_observation_state_diff

UMD_144_BUILD_ID="UMD-144"
UMD_144_REVISION="UMD_144_OBSERVATION_CHANGE_REGISTRY_V1"
UMD_144_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

CHANGE_TYPES=(
    "canonical-added",
    "canonical-removed",
    "cluster-added",
    "cluster-removed",
    "contradiction-added",
    "contradiction-removed",
)

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ObservationChangeRecord:
    change_type:str
    subject_key:str
    diff_hash:str

    def __post_init__(self):
        if self.change_type not in CHANGE_TYPES:
            raise ValueError("unsupported change type")
        if not isinstance(self.subject_key,str) or not self.subject_key:
            raise ValueError("subject_key must be non-empty")

    @property
    def change_hash(self)->str:
        return deterministic_sha256({
            "change_type":self.change_type,
            "subject_key":self.subject_key,
            "diff_hash":self.diff_hash,
        })

@dataclass(frozen=True,slots=True)
class ObservationChangeRegistry:
    diffs:Tuple[ObservationStateDiff,...]
    changes:Tuple[ObservationChangeRecord,...]
    type_index:Mapping[str,Tuple[str,...]]
    observation_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"diffs",tuple(self.diffs))
        object.__setattr__(self,"changes",tuple(self.changes))
        object.__setattr__(self,"type_index",_freeze(self.type_index))
        object.__setattr__(self,"observation_index",_freeze(self.observation_index))
        if self.diffs!=tuple(sorted(self.diffs,key=lambda d:d.diff_hash)):
            raise ValueError("diffs must be deterministically sorted")
        if self.changes!=tuple(sorted(self.changes,key=lambda c:(c.change_type,c.subject_key,c.diff_hash))):
            raise ValueError("changes must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_144_BUILD_ID:
            raise ValueError("lineage must belong to UMD-144")
        required={d.diff_hash for d in self.diffs}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every diff hash")

    def subjects_for_type(self,change_type:str)->Tuple[str,...]:
        return self.type_index.get(change_type,())

    def changes_for_observation(self,observation_id:str)->Tuple[str,...]:
        return self.observation_index.get(observation_id,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "diff_hashes":tuple(d.diff_hash for d in self.diffs),
            "change_hashes":tuple(c.change_hash for c in self.changes),
            "type_index":self.type_index,
            "observation_index":self.observation_index,
            "lineage":self.lineage,
        })

class ObservationChangeRegistryBuilder:
    __slots__=()

    def build(self,diffs:Iterable[ObservationStateDiff],*,lineage_factory)->ObservationChangeRegistry:
        values=tuple(diffs)
        if any(not isinstance(d,ObservationStateDiff) for d in values):
            raise TypeError("diffs must contain ObservationStateDiff")
        values=tuple(sorted(values,key=lambda d:d.diff_hash))

        changes=[]
        type_index={}
        observation_index={}

        def add(kind,subject,diff_hash,obs_ids=()):
            record=ObservationChangeRecord(kind,subject,diff_hash)
            changes.append(record)
            type_index.setdefault(kind,[]).append(subject)
            for obs in obs_ids:
                observation_index.setdefault(obs,[]).append(record.change_hash)

        for diff in values:
            for obs in diff.added_canonical_ids:
                add("canonical-added",obs,diff.diff_hash,(obs,))
            for obs in diff.removed_canonical_ids:
                add("canonical-removed",obs,diff.diff_hash,(obs,))
            for cluster in diff.added_cluster_ids:
                add("cluster-added",cluster,diff.diff_hash)
            for cluster in diff.removed_cluster_ids:
                add("cluster-removed",cluster,diff.diff_hash)
            for left,right in diff.added_contradictions:
                subject=left+"|"+right
                add("contradiction-added",subject,diff.diff_hash,(left,right))
            for left,right in diff.removed_contradictions:
                subject=left+"|"+right
                add("contradiction-removed",subject,diff.diff_hash,(left,right))

        changes.sort(key=lambda c:(c.change_type,c.subject_key,c.diff_hash))
        for index in (type_index,observation_index):
            for key,items in index.items():
                index[key]=tuple(sorted(set(items)))

        lineage=lineage_factory(tuple(d.diff_hash for d in values))
        return ObservationChangeRegistry(values,tuple(changes),type_index,observation_index,lineage)

def build_umd_144_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_144_BUILD_ID,"revision":UMD_144_REVISION,
        "schema_version":UMD_144_SCHEMA_VERSION,"upstream_builds":("UMD-143",),
        "mode":"deterministic_read_only_observation_change_registry",
        "change_types":CHANGE_TYPES,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_144_observation_change_registry()->bool:
    if verify_umd_143_observation_state_diff() is not True:
        return False
    m=build_umd_144_certification_manifest()
    return m["build_id"]=="UMD-144" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
