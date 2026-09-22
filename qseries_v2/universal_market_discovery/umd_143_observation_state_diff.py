from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_142_observation_state_snapshot import ObservationStateSnapshot,verify_umd_142_observation_state_snapshot

UMD_143_BUILD_ID="UMD-143"
UMD_143_REVISION="UMD_143_OBSERVATION_STATE_DIFF_V1"
UMD_143_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ObservationStateDiff:
    before_snapshot_hash:str
    after_snapshot_hash:str
    added_canonical_ids:Tuple[str,...]
    removed_canonical_ids:Tuple[str,...]
    added_cluster_ids:Tuple[str,...]
    removed_cluster_ids:Tuple[str,...]
    added_contradictions:Tuple[Tuple[str,str],...]
    removed_contradictions:Tuple[Tuple[str,str],...]
    lineage:ImmutableLineage

    def __post_init__(self):
        for name in (
            "added_canonical_ids","removed_canonical_ids","added_cluster_ids","removed_cluster_ids",
            "added_contradictions","removed_contradictions"
        ):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        if set(self.added_canonical_ids)&set(self.removed_canonical_ids):
            raise ValueError("canonical id cannot be both added and removed")
        if set(self.added_cluster_ids)&set(self.removed_cluster_ids):
            raise ValueError("cluster id cannot be both added and removed")
        if set(self.added_contradictions)&set(self.removed_contradictions):
            raise ValueError("contradiction cannot be both added and removed")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_143_BUILD_ID:
            raise ValueError("lineage must belong to UMD-143")
        required={self.before_snapshot_hash,self.after_snapshot_hash}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include both snapshot hashes")

    @property
    def empty(self)->bool:
        return not any((
            self.added_canonical_ids,self.removed_canonical_ids,
            self.added_cluster_ids,self.removed_cluster_ids,
            self.added_contradictions,self.removed_contradictions,
        ))

    @property
    def diff_hash(self)->str:
        return deterministic_sha256({
            "before_snapshot_hash":self.before_snapshot_hash,
            "after_snapshot_hash":self.after_snapshot_hash,
            "added_canonical_ids":self.added_canonical_ids,
            "removed_canonical_ids":self.removed_canonical_ids,
            "added_cluster_ids":self.added_cluster_ids,
            "removed_cluster_ids":self.removed_cluster_ids,
            "added_contradictions":self.added_contradictions,
            "removed_contradictions":self.removed_contradictions,
            "lineage":self.lineage,
        })

class ObservationStateDiffer:
    __slots__=()

    def diff(
        self,
        before:ObservationStateSnapshot,
        after:ObservationStateSnapshot,
        *,
        lineage:ImmutableLineage,
    )->ObservationStateDiff:
        if not isinstance(before,ObservationStateSnapshot) or not isinstance(after,ObservationStateSnapshot):
            raise TypeError("before and after must be ObservationStateSnapshot")
        if after.as_of<before.as_of:
            raise ValueError("after snapshot must not precede before snapshot")

        before_obs=set(before.canonical_observation_ids)
        after_obs=set(after.canonical_observation_ids)
        before_clusters=set(before.cluster_ids)
        after_clusters=set(after.cluster_ids)
        before_contra=set(before.contradiction_pairs)
        after_contra=set(after.contradiction_pairs)

        return ObservationStateDiff(
            before.snapshot_hash,
            after.snapshot_hash,
            tuple(sorted(after_obs-before_obs)),
            tuple(sorted(before_obs-after_obs)),
            tuple(sorted(after_clusters-before_clusters)),
            tuple(sorted(before_clusters-after_clusters)),
            tuple(sorted(after_contra-before_contra)),
            tuple(sorted(before_contra-after_contra)),
            lineage,
        )

def build_umd_143_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_143_BUILD_ID,"revision":UMD_143_REVISION,
        "schema_version":UMD_143_SCHEMA_VERSION,"upstream_builds":("UMD-142",),
        "mode":"deterministic_read_only_observation_state_diff",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_143_observation_state_diff()->bool:
    if verify_umd_142_observation_state_snapshot() is not True:
        return False
    m=build_umd_143_certification_manifest()
    return m["build_id"]=="UMD-143" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
